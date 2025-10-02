from logging import getLogger
from datetime import datetime

import pytest
from playwright.sync_api import Page, expect
import uuid


from helpers.base_client.base_client import HTTPError

logger = getLogger(__name__)


class Locators:
    list_view_button = ("rect:nth-child(3)",)
    icon_view_button = ("rect:nth-child(6)",)


class TestDocumentsAPI:
    def test_upload_and_delete_file(self, file_tracker, tmp_path):
        created_files, client = file_tracker
        try:
            file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
            assert file_info["status"] is True
            assert "id" in file_info
            assert "file_name" in file_info
            search = client.search_files()
            ids = [f["id"] for f in search["data"]]
            assert file_info["id"] in ids
            delete_result = client.delete_files([file_info["id"]])
            assert delete_result[0]["status"] is True
            assert delete_result[0]["action"] == "delete"
            search_after = client.search_files()
            ids_after = [f["id"] for f in search_after["data"]]
            assert file_info["id"] not in ids_after
            created_files.clear()
        finally:
            if temp_file.exists():
                temp_file.unlink()

    @pytest.mark.skip(reason="Returns 500 instead of 4xx")
    def test_upload_invalid_format(self, file_client, tmp_path):
        invalid_file = tmp_path / f"{uuid.uuid4().hex}.py"
        invalid_file.write_text("this is py file")

        with pytest.raises(HTTPError) as exc:
            file_client.upload_file(str(invalid_file))

        assert exc.value.status_code == 400

    @pytest.mark.skip(reason="Uploads a file, but returns 500")
    @pytest.mark.parametrize("content", ["", " "])
    def test_upload_empty_file(self, file_client, tmp_path, content):
        empty_file = tmp_path / f"{uuid.uuid4().hex}_empty.pdf"
        empty_file.write_text(content)
        with pytest.raises(HTTPError) as exc:
            file_client.upload_file(str(empty_file))
        assert exc.value.status_code == 400

    def test_move_file(self, file_tracker, dataset_tracker, tmp_path):
        created_datasets, dataset_client = dataset_tracker

        first_dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        second_dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"

        first_resp = dataset_client.create_dataset(name=first_dataset_name)
        created_datasets.append(first_dataset_name)
        assert "successfully created" in first_resp["detail"].lower()
        first_dataset_id = dataset_client.search(
            filters=[{"field": "name", "operator": "eq", "value": first_dataset_name}]
        )["data"][0]["id"]

        second_resp = dataset_client.create_dataset(name=second_dataset_name)
        created_datasets.append(second_dataset_name)
        assert "successfully created" in second_resp["detail"].lower()
        second_dataset_id = dataset_client.search(
            filters=[{"field": "name", "operator": "eq", "value": second_dataset_name}]
        )["data"][0]["id"]

        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        file_id = file_info["id"]
        try:
            move1 = client.move_files(name=first_dataset_name, objects=[file_id])[0]
            assert move1["status"] is True
            assert "successfully bounded" in move1["message"].lower()
            files_in_first = dataset_client.search_files(dataset_id=first_dataset_id)["data"]
            assert any(f["id"] == file_id for f in files_in_first)
            move2 = client.move_files(name=second_dataset_name, objects=[file_id])[0]
            assert move2["status"] is True
            assert "successfully bounded" in move2["message"].lower()
            files_in_second = dataset_client.search_files(dataset_id=second_dataset_id)["data"]
            assert any(f["id"] == file_id for f in files_in_second)
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_add_file_to_dataset_twice(self, file_tracker, dataset_tracker, tmp_path):
        created_datasets, dataset_client = dataset_tracker
        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        dataset = dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)
        assert "successfully created" in dataset["detail"].lower()
        first_dataset_id = dataset_client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])[
            "data"
        ][0]["id"]

        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        file_id = file_info["id"]
        try:
            move1 = client.move_files(name=dataset_name, objects=[file_id])[0]
            assert move1["status"] is True
            assert "successfully bounded" in move1["message"].lower()
            files_in_first = dataset_client.search_files(dataset_id=first_dataset_id)["data"]
            assert any(f["id"] == file_id for f in files_in_first)
            move2 = client.move_files(name=dataset_name, objects=[file_id])[0]
            assert move2["status"] is False
            assert "already bounded" in move2["message"].lower()
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_clear_search_files(self, file_tracker, tmp_path):
        created_files, client = file_tracker
        result = client.search_files()
        assert "pagination" in result
        assert "data" in result
        assert isinstance(result["data"], list)
        pagination = result["pagination"]
        required_pagination_keys = {"page_num", "page_offset", "page_size", "min_pages_left", "total", "has_more"}
        assert required_pagination_keys <= pagination.keys()
        for file in result["data"]:
            required_file_keys = {
                "id",
                "original_name",
                "bucket",
                "size_in_bytes",
                "extension",
                "original_ext",
                "content_type",
                "pages",
                "last_modified",
                "status",
                "path",
                "datasets",
            }
            assert required_file_keys <= file.keys()
            assert isinstance(file["id"], int)
            assert isinstance(file["original_name"], str)
            assert isinstance(file["size_in_bytes"], int)

    def test_search_existing_file(self, file_tracker, tmp_path):
        created_files, client = file_tracker
        try:
            file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
            assert file_info["status"] is True
            search_resp = client.search_files(
                filters=[{"field": "original_name", "operator": "eq", "value": file_info["file_name"]}]
            )
            names = [f["original_name"] for f in search_resp["data"]]
            assert file_info["file_name"] in names
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_search_non_existing_file(self, file_client):
        search_resp = file_client.search_files(
            filters=[{"field": "original_name", "operator": "eq", "value": "definitely_not_a_file.pdf"}]
        )
        assert search_resp["data"] == []

    def test_search_multiple_existing_files(self, file_tracker, tmp_path):
        created_files, client = file_tracker
        f1, t1 = client.upload_temp_file(client, file_tracker, tmp_path)
        f2, t2 = client.upload_temp_file(client, file_tracker, tmp_path)
        names = [f1["file_name"], f2["file_name"]]

        search = client.search_files(filters=[{"field": "original_name", "operator": "in", "value": names}])
        found_names = {f["original_name"] for f in search["data"]}
        assert set(names) <= found_names

        t1.unlink(missing_ok=True)
        t2.unlink(missing_ok=True)

    def test_download_existing_file(self, file_tracker, tmp_path):
        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        file_id = file_info["id"]

        content = client.download_file(file_id)
        assert isinstance(content, (bytes, bytearray))
        assert len(content) > 100
        assert content.startswith(b"%PDF")

        temp_file.unlink(missing_ok=True)

    def test_download_nonexistent_file(self, file_client):
        with pytest.raises(HTTPError) as exc:
            file_client.download_file(9999999)
        assert exc.value.status_code == 404

    @pytest.mark.parametrize("field", ["original_name", "last_modified", "size_in_bytes"])
    @pytest.mark.parametrize("direction", ["asc", "desc"])
    # name descending fails
    def test_files_sorting(self, file_client, field, direction):
        resp = file_client.post_json(
            "/assets/files/search",
            json={
                "pagination": {"page_num": 1, "page_size": 15},
                "filters": [{"field": "original_name", "operator": "ilike", "value": "%%"}],
                "sorting": [{"direction": direction, "field": field}],
            },
            headers=file_client._default_headers(content_type_json=True),
        )

        data = resp["data"]
        values = [d[field] for d in data if field in d]

        if field == "last_modified":
            values = [datetime.fromisoformat(v) for v in values]

        if field == "size_in_bytes":
            values = [int(v) for v in values]

        expected = sorted(values, reverse=(direction == "desc"))
        assert values == expected, f"{field} not sorted {direction}"


class TestDocumentsFrontend:
    def test_documents_scroll(self, logged_in_page: Page):
        page = logged_in_page

        last_doc = page.locator('a[class*="document-card-view-item_card-item"]').last
        last_doc.scroll_into_view_if_needed()
        expect(last_doc).to_be_visible()

        first_doc = page.locator('a[class*="document-card-view-item_card-item"]').first
        first_doc.scroll_into_view_if_needed()
        expect(first_doc).to_be_visible()

    def test_documents_pagination_by_page_number(self, logged_in_page: Page):
        page = logged_in_page

        nav = page.locator('nav[role="navigation"]')
        nav.wait_for(state="visible", timeout=10000)
        list_selector = 'a[class*="document-card-view-item_card-item"]'
        first_doc = page.locator(list_selector).first
        expect(first_doc).to_be_visible(timeout=10000)

        old_text = first_doc.text_content()

        nav.get_by_role("button", name="2", exact=True).click()

        try:
            expect(nav.get_by_role("button", name="2")).to_have_attribute("aria-current", "true", timeout=10000)
        except AssertionError:
            expect(page.locator(list_selector).first).not_to_have_text(old_text, timeout=10000)

        active_attr = nav.get_by_role("button", name="2").get_attribute("aria-current")
        assert active_attr == "true" or page.locator(list_selector).first.text_content() != old_text

    def test_documents_pagination_by_arrows(self, logged_in_page: Page):
        page = logged_in_page

        nav = page.locator('nav[role="navigation"]')
        nav.wait_for(state="visible", timeout=10000)
        list_selector = 'a[class*="document-card-view-item_card-item"]'
        first_doc = page.locator(list_selector).first
        expect(first_doc).to_be_visible(timeout=10000)

        old_text = first_doc.text_content()

        nav.locator("button").last.click()
        try:
            expect(nav.get_by_role("button", name="2", exact=True)).to_have_attribute(
                "aria-current", "true", timeout=10000
            )
        except AssertionError:
            expect(page.locator(list_selector).first).not_to_have_text(old_text, timeout=10000)

        old_text_back = page.locator(list_selector).first.text_content()
        nav.locator("button").first.click()
        try:
            expect(nav.get_by_role("button", name="1", exact=True)).to_have_attribute(
                "aria-current", "true", timeout=10000
            )
        except AssertionError:
            expect(page.locator(list_selector).first).not_to_have_text(old_text_back, timeout=10000)

        active_attr_1 = nav.get_by_role("button", name="1", exact=True).get_attribute("aria-current")
        assert active_attr_1 == "true" or page.locator(list_selector).first.text_content() != old_text_back

    def test_documents_show_on_page(self, logged_in_page: Page):
        page = logged_in_page

        list_selector = 'a[class*="document-card-view-item_card-item"]'
        cards = page.locator(list_selector)

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

            expect(cards.first).to_be_visible(timeout=10000)
            count = cards.count()
            assert count <= int(value), f"Expected at most {value} cards, got {count}"

    @pytest.mark.parametrize(
        "flow",
        [
            {"after_cancel": "Discard"},
            {"after_cancel": "Save"},
            {"choose_first": True, "after_cancel": None},
        ],
    )
    def test_add_to_dataset_cancel(self, logged_in_page: Page, flow):
        page = logged_in_page
        first_card = page.locator("a[class*='document-card-view-item_card-item']").first
        expect(first_card).to_be_visible(timeout=10000)
        first_card.scroll_into_view_if_needed()
        input_el = first_card.locator("input[type='checkbox']").first
        label = first_card.locator("label.uui-checkbox-container")
        uui_div = first_card.locator("div.uui-checkbox")

        click_target = label.first if label.count() else uui_div.first if uui_div.count() else input_el
        click_target.click(force=True)
        expect(input_el).to_be_checked(timeout=5000)

        page.get_by_role("button", name="Add to dataset").click()
        dataset_input = page.get_by_role("textbox", name="Please select dataset")
        dataset_input.click()
        first_option = page.locator("div[role='option']").first
        first_option.wait_for(state="visible", timeout=5000)
        first_option.click()

        if flow.get("choose_first"):
            page.get_by_role("button", name="Choose").click()
        page.get_by_role("button", name="Cancel").click()

        if flow.get("after_cancel"):
            page.get_by_role("button", name=flow["after_cancel"]).click()

        expect(page.get_by_role("button", name="Choose")).not_to_be_visible(timeout=5000)

    def test_click_preprocess(self, logged_in_page: Page):
        page = logged_in_page
        first_card = page.locator("a[class*='document-card-view-item_card-item']").first
        expect(first_card).to_be_visible(timeout=10000)
        first_card.scroll_into_view_if_needed()
        input_el = first_card.locator("input[type='checkbox']").first
        label = first_card.locator("label.uui-checkbox-container")
        uui_div = first_card.locator("div.uui-checkbox")

        click_target = label.first if label.count() else uui_div.first if uui_div.count() else input_el
        click_target.click(force=True)
        expect(input_el).to_be_checked(timeout=5000)

        preprocess_btn = page.get_by_role("button", name="Preprocess")
        expect(preprocess_btn).to_be_visible(timeout=5000)
        preprocess_btn.click()
        # what are we checking?

    def test_add_to_extraction(
        self,
        logged_in_page: Page,
        jobs_client,
    ):
        page = logged_in_page

        first_card = page.locator("a[class*='document-card-view-item_card-item']").first
        expect(first_card).to_be_visible(timeout=10000)
        first_card.scroll_into_view_if_needed()

        checkbox = first_card.locator("input[type='checkbox']").first
        label = first_card.locator("label.uui-checkbox-container")
        uui_div = first_card.locator("div.uui-checkbox")

        click_target = label.first if label.count() else uui_div.first if uui_div.count() else checkbox
        click_target.click(force=True)
        expect(checkbox).to_be_checked(timeout=5000)

        page.get_by_role("button", name="Add to extraction").click()

        first_cell = page.get_by_role("cell").first
        first_cell.locator("label div").click()
        expect(first_cell.locator("input[type='checkbox']")).to_be_checked(timeout=5000)

        page.get_by_role("button", name="Next").click()

        job_name = f"extraction_job_{uuid.uuid4().hex[:8]}"
        page.get_by_role("textbox", name="Job name").fill(job_name)
        page.get_by_role("textbox", name="Select pipeline").click()
        page.get_by_text("print", exact=True).click()

        page.get_by_role("button", name="Start Extraction").click()

        page.wait_for_url("**/jobs/**", timeout=20000)
        jobs = jobs_client.search_jobs()
        job_id = next((j["id"] for j in jobs["data"] if j["name"] == job_name), None)
        assert job_id, f"Job with name {job_name} not found!"
        jobs_client.poll_until_finished(job_id, timeout_seconds=180)
        page.reload()
        expect(page.get_by_text("Finished")).to_be_visible(timeout=10000)

    @pytest.mark.parametrize("num_files", [1, 3])
    @pytest.mark.parametrize("view_mode", ["card", "list"])
    def test_delete_files(self, logged_in_page: Page, file_tracker, tmp_path, num_files, view_mode):
        # list view fails because deleted lines does not disappear
        page = logged_in_page
        created_files, client = file_tracker
        temp_files = []
        uploaded_files = []

        for _ in range(num_files):
            file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
            assert file_info["status"] is True
            uploaded_files.append(file_info)
            temp_files.append(temp_file)

        page.reload()

        if view_mode == "list":
            page.locator("rect").nth(1).click(force=True)
            rows_selector = "div.uui-table-row-container[role='row']"
            items = page.locator(rows_selector)
        else:
            cards_selector = 'a[class*="document-card-view-item_card-item"]'
            items = page.locator(cards_selector)

        expect(items.first).to_be_visible(timeout=10000)

        selected_names = []
        for f in uploaded_files:
            name = f["file_name"]
            element = items.filter(has_text=name).first
            expect(element).to_be_visible(timeout=10000)

            checkbox = element.locator("input[type='checkbox']").first
            label = element.locator("label.uui-checkbox-container")
            uui_div = element.locator("div.uui-checkbox")
            click_target = label.first if label.count() else uui_div.first if uui_div.count() else checkbox

            element.scroll_into_view_if_needed()
            click_target.click(force=True)
            expect(checkbox).to_be_checked(timeout=5000)

            selected_names.append(name)

        delete_button = page.get_by_role("button", name="Delete")
        delete_button.click(force=True)

        for name in selected_names:
            expect(page.get_by_text(name)).not_to_be_visible(timeout=10000)

        remaining = client.search_files()["data"]
        remaining_ids = {f["id"] for f in remaining}
        for f in uploaded_files:
            assert f["id"] not in remaining_ids, f"File {f['file_name']} was not deleted"
        for f in created_files:
            if f not in uploaded_files:
                assert f["id"] in remaining_ids, f"Unrelated file {f['file_name']} was deleted"

        for temp in temp_files:
            if temp.exists():
                temp.unlink()

    @pytest.mark.parametrize("rect_index", [0, 1])
    def test_select_all_unselect_all_both_views(self, logged_in_page, rect_index):
        page = logged_in_page
        page.locator("rect").nth(rect_index).click(force=True)
        select_all = page.locator("label:has-text('Select All') div").first
        select_all.click(force=True)
        file_inputs = page.locator("div.uui-checkbox > input[type='checkbox']")
        for i in range(file_inputs.count()):
            expect(file_inputs.nth(i)).to_be_checked()
        select_all = page.locator("label:has-text('selected') div").first
        select_all.click(force=True)
        file_inputs = page.locator("div.uui-checkbox > input[type='checkbox']")
        for i in range(file_inputs.count()):
            expect(file_inputs.nth(i)).not_to_be_checked()

    @pytest.mark.parametrize(
        "rect_index, file_locator",
        [
            (0, "a[class^='document-card-view-item_card-item']"),
            (1, "div[role='cell']"),
        ],
    )
    def test_view_switch(self, logged_in_page: Page, rect_index: int, file_locator: str):
        page = logged_in_page
        page.locator("rect").nth(rect_index).click(force=True)
        expect(page.locator(file_locator).first).to_be_visible()

    @pytest.mark.parametrize("action", ["select", "unselect"])
    def test_select_unselect_one_by_one_icon_view(self, logged_in_page: Page, action: str):
        page = logged_in_page

        page.locator("rect").nth(0).click(force=True)

        items = page.locator("a[class^='document-card-view-item_card-item']")
        expect(items.first).to_be_visible(timeout=10000)

        inputs = items.locator("input[type='checkbox']")

        if action == "unselect":
            page.locator("label:has-text('Select All') div").first.click(force=True)
            expect(inputs.first).to_be_checked(timeout=5000)

        count = inputs.count()
        for i in range(count):
            row = items.nth(i)
            row.scroll_into_view_if_needed()

            input_el = row.locator("input[type='checkbox']").first
            label = row.locator("label.uui-checkbox-container")
            uui_div = row.locator("div.uui-checkbox")

            click_target = label.first if label.count() else uui_div.first if uui_div.count() else input_el
            click_target.click(force=True)

            if action == "select":
                expect(input_el).to_be_checked()
            else:
                expect(input_el).not_to_be_checked()

    @pytest.mark.parametrize("action", ["select", "unselect"])
    def test_select_unselect_one_by_one_list_view(self, logged_in_page: Page, action: str):
        page = logged_in_page
        page.locator("rect").nth(1).click(force=True)

        rows = page.locator("div.uui-table-row-container[role='row']")
        expect(rows.first).to_be_visible(timeout=5000)

        count = rows.count()
        assert count > 0, "no list rows found"

        if action == "unselect":
            page.locator("label:has-text('Select All') div").first.click(force=True)
            expect(page.locator("div.uui-checkbox > input[type='checkbox']").first).to_be_checked(timeout=5000)

        checkboxes = page.locator("div.uui-checkbox")
        count = checkboxes.count()
        for i in range(2, count):
            cb = checkboxes.nth(i)
            cb.scroll_into_view_if_needed()
            cb.click(force=True)

            if action == "select":
                expect(cb).to_be_checked()
            else:
                expect(cb).not_to_be_checked()
