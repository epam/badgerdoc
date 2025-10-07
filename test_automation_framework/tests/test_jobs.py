from logging import getLogger
from datetime import datetime, timedelta
import uuid
from playwright.sync_api import Page, expect
from helpers.steps.jobs_creation import (
    run_new_job_documents_workflow,
    run_new_job_first_line_workflow,
    run_new_job_multi_tab_workflow,
    run_new_job_dataset_without_documents_workflow,
)
from helpers.base_client.base_client import HTTPError

import pytest
import re


logger = getLogger(__name__)


class TestJobs:
    def test_create_and_poll_job(
        self, file_client, jobs_client, file_tracker, dataset_tracker, job_tracker, tmp_path, user_uuid
    ):
        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_ds_{uuid.uuid4().hex[:8]}"
        dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)
        move_resp = file_client.move_files(name=dataset_name, objects=[file_info["id"]])[0]
        assert move_resp["status"] is True
        job_name = f"test_job_{uuid.uuid4().hex[:8]}"
        create_resp = jobs_client.create_job(
            name=job_name,
            file_ids=[file_info["id"]],
            owners=[user_uuid],
        )
        job_tracker[0].append(create_resp)
        job_id = create_resp.get("id")
        assert job_id
        final_job = jobs_client.poll_until_finished(job_id=job_id, timeout_seconds=300)
        status = final_job.get("status")
        assert str(status).lower() in {"finished", "success", "completed"}
        job_files = final_job.get("files") or []
        assert file_info["id"] in job_files

    @pytest.mark.parametrize("field", ["name", "type", "status", "deadline", "creation_datetime"])
    @pytest.mark.parametrize("direction", ["asc", "desc"])
    # descending name sorting works weird
    def test_jobs_sorting(self, jobs_client, field, direction):
        resp = jobs_client.post_json(
            "/jobs/jobs/search",
            json={
                "pagination": {"page_num": 1, "page_size": 15},
                "filters": [],
                "sorting": [{"direction": direction, "field": field}],
            },
            headers=jobs_client._default_headers(content_type_json=True),
        )
        data = resp["data"]
        values = [d[field] for d in data if field in d and d[field] is not None]

        if field in {"creation_datetime", "deadline"}:
            values = [datetime.fromisoformat(v) for v in values]

        expected = sorted(values, reverse=(direction == "desc"))
        assert values == expected

    @pytest.mark.parametrize("field", ["name", "type", "status", "deadline", "creation_datetime"])
    def test_job_search(self, jobs_client, job_tracker, file_tracker, dataset_tracker, user_uuid, tmp_path, field):
        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_ds_{uuid.uuid4().hex[:8]}"
        dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)

        job_name = f"test_job_{uuid.uuid4().hex[:8]}"
        create_resp = jobs_client.create_job(
            name=job_name,
            file_ids=[file_info["id"]],
            owners=[user_uuid],
        )
        job_id = create_resp.get("id")
        jobs_client.poll_until_finished(job_id=job_id, timeout_seconds=300)
        job_tracker[0].append(create_resp)
        search_value = create_resp.get(field, None)

        filters = [
            {"field": field, "operator": "eq", "value": search_value},
            {"field": "name", "operator": "eq", "value": job_name},
        ]

        search_resp = jobs_client.post_json(
            "/jobs/jobs/search",
            json={
                "pagination": {"page_num": 1, "page_size": 100},
                "filters": filters,
            },
            headers=jobs_client._default_headers(content_type_json=True),
        )

        job_ids = [j["id"] for j in search_resp["data"]]
        assert job_id in job_ids

    @pytest.mark.parametrize("field", ["creation_datetime", "deadline"])
    def test_jobs_date_range_filter(self, jobs_client, field):
        start = (datetime.utcnow() - timedelta(days=365)).replace(microsecond=0).isoformat()
        end = (datetime.utcnow() + timedelta(days=365)).replace(microsecond=0).isoformat()

        resp = jobs_client.post_json(
            "/jobs/jobs/search",
            json={
                "pagination": {"page_num": 1, "page_size": 15},
                "filters": [
                    {"field": field, "operator": "ge", "value": start},
                    {"field": field, "operator": "le", "value": end},
                ],
            },
            headers=jobs_client._default_headers(content_type_json=True),
        )

        data = resp["data"]
        for job in data:
            if field in job and job[field] is not None:
                date_val = datetime.fromisoformat(job[field])
                assert datetime.fromisoformat(start) <= date_val <= datetime.fromisoformat(end)

    def test_create_job_with_existing_name(
        self, file_client, jobs_client, file_tracker, dataset_tracker, job_tracker, tmp_path, user_uuid
    ):
        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_ds_{uuid.uuid4().hex[:8]}"
        dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)
        move_resp = file_client.move_files(name=dataset_name, objects=[file_info["id"]])[0]
        assert move_resp["status"] is True
        job_name = f"test_job_{uuid.uuid4().hex[:8]}"
        create_resp_first = jobs_client.create_job(
            name=job_name,
            file_ids=[file_info["id"]],
            owners=[user_uuid],
        )
        job_tracker[0].append(create_resp_first)
        job_id = create_resp_first.get("id")
        assert job_id

        with pytest.raises(HTTPError) as exc:
            jobs_client.create_job(
                name=job_name,
                file_ids=[file_info["id"]],
                owners=[user_uuid],
            )
        assert exc.value.status_code == 400


class TestJobsFrontend:
    def test_jobs_scroll(self, jobs_page: Page):
        page = jobs_page

        page_size_container = page.locator("div:has(> div > span:has-text('Show on page'))")
        page_size_input = page_size_container.locator("input[aria-haspopup='true']")
        page_size_input.click()
        page.locator("div[role='option']", has_text="100").click()

        rows = page.locator("div[role='row']").filter(has_not=page.locator("div[role='columnheader']"))

        last_row = rows.last
        last_row.scroll_into_view_if_needed()
        expect(last_row).to_be_visible()

        first_row = rows.first
        first_row.scroll_into_view_if_needed()
        expect(first_row).to_be_visible()

    def test_jobs_pagination_by_page_number(self, jobs_page: Page):
        page = jobs_page
        nav = page.locator('nav[role="navigation"]')
        nav.wait_for(state="visible", timeout=10000)

        rows = page.locator("div[role='row']").filter(has_not=page.locator("div[role='columnheader']"))
        first_row = rows.first
        expect(first_row).to_be_visible(timeout=10000)

        old_text = first_row.text_content()

        nav.get_by_role("button", name="2", exact=True).click()

        try:
            expect(nav.get_by_role("button", name="2")).to_have_attribute("aria-current", "true", timeout=10000)
        except AssertionError:
            expect(rows.first).not_to_have_text(old_text, timeout=10000)

        active_attr = nav.get_by_role("button", name="2").get_attribute("aria-current")
        assert active_attr == "true" or rows.first.text_content() != old_text

    def test_jobs_pagination_by_arrows(self, jobs_page: Page):
        page = jobs_page

        nav = page.locator('nav[role="navigation"]')
        nav.wait_for(state="visible", timeout=10000)

        rows = page.locator("div[role='row']").filter(has_not=page.locator("div[role='columnheader']"))
        first_row = rows.first
        expect(first_row).to_be_visible(timeout=10000)

        old_text = first_row.text_content()

        nav.locator("button").last.click()
        try:
            expect(nav.get_by_role("button", name="2", exact=True)).to_have_attribute(
                "aria-current", "true", timeout=10000
            )
        except AssertionError:
            expect(rows.first).not_to_have_text(old_text, timeout=10000)

        old_text_back = rows.first.text_content()
        nav.locator("button").first.click()
        try:
            expect(nav.get_by_role("button", name="1", exact=True)).to_have_attribute(
                "aria-current", "true", timeout=10000
            )
        except AssertionError:
            expect(rows.first).not_to_have_text(old_text_back, timeout=10000)

        active_attr_1 = nav.get_by_role("button", name="1", exact=True).get_attribute("aria-current")
        assert active_attr_1 == "true" or rows.first.text_content() != old_text_back

    def test_jobs_show_on_page(self, jobs_page: Page):
        page = jobs_page

        rows = page.locator("div[role='row']").locator("xpath=..").locator("div[role='row']:not(.uui-table-header-row)")

        page_size_container = page.locator("div:has(> div > span:has-text('Show on page'))")
        page_size_input = page_size_container.locator("input[aria-haspopup='true']")

        page_size_input.click()
        options = page.locator("div[role='option']")
        option_texts = [options.nth(i).inner_text() for i in range(options.count())]
        page_size_input.click()

        for value in option_texts:
            page_size_input.click()

            option = page.locator("div[role='option']", has_text=value).first
            option.wait_for(state="visible", timeout=5000)
            option.click()

            expect(rows.first).to_be_visible(timeout=10000)
            count = rows.count()
            assert count <= int(value), f"Expected at most {value} rows, got {count}"

    @pytest.mark.parametrize("num_files", [1, 3])
    @pytest.mark.parametrize("manager", ["Airflow", "Databricks", "Other"])
    def test_create_job_documents_tab(
        self, jobs_page: Page, file_tracker, tmp_path, jobs_client, file_client, dataset_tracker, num_files, manager
    ):
        page = jobs_page
        run_new_job_documents_workflow(
            page=page,
            num_files=num_files,
            file_tracker=file_tracker,
            dataset_tracker=dataset_tracker,
            jobs_client=jobs_client,
            tmp_path=tmp_path,
            pipeline_manager=manager,
        )

    @pytest.mark.parametrize("manager", ["Airflow", "Databricks"])
    @pytest.mark.parametrize("tab", ["Jobs", "Datasets", "Revisions"])
    def test_create_job_other_tabs(
        self, jobs_page: Page, file_tracker, tmp_path, jobs_client, file_client, tab, manager, dataset_tracker
    ):
        page = jobs_page
        run_new_job_first_line_workflow(
            page=page,
            num_files=1,
            file_tracker=file_tracker,
            dataset_tracker=dataset_tracker,
            jobs_client=jobs_client,
            tmp_path=tmp_path,
            pipeline_manager=manager,
            tab_button=tab,
        )

    @pytest.mark.parametrize("manager", ["Airflow", "Databricks"])
    @pytest.mark.parametrize(
        "tabs",
        [
            ["Documents", "Jobs"],
            ["Documents", "Datasets"],
            ["Documents", "Revisions"],
            ["Documents", "Jobs", "Datasets", "Revisions"],
        ],
    )
    def test_create_job_multi_tabs(
        self, jobs_page: Page, file_tracker, tmp_path, jobs_client, dataset_tracker, manager, tabs
    ):
        page = jobs_page
        run_new_job_multi_tab_workflow(
            page=page,
            jobs_client=jobs_client,
            tabs=tabs,
            file_tracker=file_tracker,
            dataset_tracker=dataset_tracker,
            tmp_path=tmp_path,
            pipeline_manager=manager,
        )

    def test_create_job_zero_dataset(
        self,
        jobs_page: Page,
        file_tracker,
        tmp_path,
        jobs_client,
        dataset_tracker,
    ):
        # outcome?
        page = jobs_page
        run_new_job_dataset_without_documents_workflow(
            page=page,
            jobs_client=jobs_client,
            dataset_tracker=dataset_tracker,
        )

    def test_create_job_without_name(
        self,
        jobs_page: Page,
    ):
        page = jobs_page
        logger.info("Open wizard")
        page.get_by_role("button", name="New job").click()
        page.get_by_role("button", name="Next").click()
        page.get_by_role("button", name="New Job").click()
        error_label = page.locator("div[role='alert'].uui-invalid-message").nth(0)
        expect(error_label).to_have_text("The field is mandatory", timeout=5000)

    def test_create_job_save_draft(
        self, jobs_page: Page, file_tracker, tmp_path, jobs_client, file_client, dataset_tracker
    ):
        page = jobs_page
        run_new_job_first_line_workflow(
            page=page,
            num_files=1,
            file_tracker=file_tracker,
            dataset_tracker=dataset_tracker,
            jobs_client=jobs_client,
            tmp_path=tmp_path,
            tab_button="Jobs",
            save_as_draft=True,
        )

    @pytest.mark.parametrize(
        "validation_type", ["Cross validation", "Extensive validation", "Hierarchical validation", "Validation only"]
    )
    def test_create_job_human_in_the_loop(
        self, jobs_page: Page, file_tracker, tmp_path, jobs_client, dataset_tracker, validation_type
    ):
        page = jobs_page
        run_new_job_documents_workflow(
            page=page,
            num_files=1,
            jobs_client=jobs_client,
            file_tracker=file_tracker,
            dataset_tracker=dataset_tracker,
            tmp_path=tmp_path,
            human_in_loop=True,
            validation_type=validation_type,
        )

    def test_create_job_human_in_the_loop_distribute(
        self, jobs_page: Page, file_tracker, tmp_path, jobs_client, dataset_tracker
    ):
        page = jobs_page
        run_new_job_documents_workflow(
            page=page,
            num_files=1,
            jobs_client=jobs_client,
            file_tracker=file_tracker,
            dataset_tracker=dataset_tracker,
            tmp_path=tmp_path,
            human_in_loop=True,
            distribute_tasks=True,
        )

    def test_open_any_job_from_table(self, jobs_page: Page):
        page = jobs_page
        rows = page.locator("div[role='row']").filter(has_not=page.locator("div[role='columnheader']"))
        expect(rows.first).to_be_visible(timeout=10000)
        first_job = rows.first.locator("div").nth(1)
        job_name = first_job.text_content().strip()
        first_job.click()
        expect(page).to_have_url(re.compile(r".*/jobs/.*"), timeout=10000)
        expect(page.get_by_text(job_name)).to_be_visible(timeout=10000)

    def test_open_job_panel_load_bar(self, jobs_page: Page):
        page = jobs_page

        rows = page.locator("div[role='row']").filter(has_not=page.locator("div[role='columnheader']"))
        expect(rows.first).to_be_visible(timeout=10000)
        rows.first.click()

        sidebar = page.locator("div[class*='job-page_job-page-sidebar-content']")
        expect(sidebar).to_be_visible(timeout=10000)

        progress_text = sidebar.locator("p[class*='job-sidebar-header_progressBarText']")
        expect(progress_text).to_be_visible(timeout=10000)

        progress_bar = sidebar.locator("div[class*='job-sidebar-header_bar']")
        count = progress_bar.count()
        assert count > 0, "Progress bar element not found in DOM"

    def test_open_job_panel_hide_unhide(self, jobs_page: Page):
        page = jobs_page

        rows = page.locator("div[role='row']").filter(has_not=page.locator("div[role='columnheader']"))
        expect(rows.first).to_be_visible(timeout=10000)
        rows.first.click()

        sidebar = page.locator("div[class*='job-page_job-page-sidebar-content']")
        expect(sidebar).to_be_visible(timeout=10000)

        panel_title = sidebar.locator("h2")
        expect(panel_title).to_have_text("Automatic", timeout=10000)

        panel_wrapper = sidebar.locator("div[class*='jod-detailed-sidebar-connector_sidebar-panel-wrapper']")
        toggle_button = sidebar.locator("button[class*='jod-detailed-sidebar-connector_close-icon']")
        expect(toggle_button).to_be_visible(timeout=5000)

        initial_classes = panel_wrapper.first.get_attribute("class") or ""
        assert "sidebar-panel-opened" in initial_classes, f"Expected opened class, got: {initial_classes}"

        toggle_button.click()

        page.wait_for_timeout(300)
        closed_classes = panel_wrapper.first.get_attribute("class") or ""
        assert "sidebar-panel-closed" in closed_classes, f"Expected closed class, got: {closed_classes}"

        open_icon_button = sidebar.locator("button[class*='jod-detailed-sidebar-connector_open-icon']")
        expect(open_icon_button).to_be_visible(timeout=5000)

        open_icon_button.click()

        page.wait_for_timeout(300)
        reopened_classes = panel_wrapper.first.get_attribute("class") or ""
        assert "sidebar-panel-opened" in reopened_classes, f"Expected reopened class, got: {reopened_classes}"
