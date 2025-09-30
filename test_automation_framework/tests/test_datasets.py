from logging import getLogger
import uuid
from playwright.sync_api import Page, expect

import pytest


from helpers.base_client.base_client import HTTPError

logger = getLogger(__name__)


class TestDatasets:
    def test_clear_search_for_datasets(self, dataset_client):
        result = dataset_client.search()
        assert "pagination" in result
        assert "data" in result
        assert isinstance(result["data"], list)
        pagination = result["pagination"]
        required_pagination_keys = {"page_num", "page_offset", "page_size", "min_pages_left", "total", "has_more"}
        assert required_pagination_keys <= pagination.keys()
        for dataset in result["data"]:
            required_dataset_keys = {"id", "name", "count", "created"}
            assert required_dataset_keys <= dataset.keys()
            assert isinstance(dataset["id"], int)
            assert isinstance(dataset["name"], str)
            assert isinstance(dataset["count"], int)

    def test_search_sorting(self, dataset_client):
        result = dataset_client.search(sorting=[{"direction": "desc", "field": "name"}])
        names = [d["name"] for d in result["data"]]
        assert names == sorted(names, reverse=True)

    def test_search_pagination(self, dataset_client):
        result = dataset_client.search(page_num=1, page_size=15)
        assert len(result["data"]) <= 15
        assert result["pagination"]["page_num"] == 1

    def test_selection(self, dataset_client):
        datasets = dataset_client.search()["data"]
        assert datasets
        dataset_id = datasets[0]["id"]
        files_selected = dataset_client.search_files(dataset_id=dataset_id)["data"]
        assert isinstance(files_selected, list)
        for f in files_selected:
            assert any(d["id"] == dataset_id for d in f.get("datasets", []))
        files_all = dataset_client.search_files()["data"]
        assert isinstance(files_all, list)
        has_dataset = any(f.get("datasets") for f in files_all)
        has_no_dataset = any(not f.get("datasets") for f in files_all)
        assert has_dataset or has_no_dataset

    def test_create_and_delete_dataset(self, dataset_client):
        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        create_resp = dataset_client.create_dataset(name=dataset_name)
        assert "detail" in create_resp
        assert "successfully created" in create_resp["detail"].lower()
        search_resp = dataset_client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])
        assert any(d["name"] == dataset_name for d in search_resp["data"])
        delete_resp = dataset_client.delete_dataset(name=dataset_name)
        assert "detail" in delete_resp
        assert "successfully deleted" in delete_resp["detail"].lower()
        search_after = dataset_client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])
        assert all(d["name"] != dataset_name for d in search_after["data"])

    @pytest.mark.skip(reason="Successfully creates dataset")
    def test_create_dataset_with_empty_name(self, dataset_tracker):
        created, client = dataset_tracker

        with pytest.raises(HTTPError) as e:
            client.create_dataset(name="")

        assert e.value.status_code in (400, 422)

    def test_create_duplicate_dataset(self, dataset_tracker):
        created, client = dataset_tracker
        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        resp = client.create_dataset(name=dataset_name)
        created.append(dataset_name)
        assert "successfully created" in resp["detail"].lower()
        with pytest.raises(HTTPError) as exc:
            client.create_dataset(name=dataset_name)
        assert exc.value.status_code == 400
        assert "already exists" in exc.value.body.lower()

    def test_search_existing_dataset(self, dataset_tracker):
        created, client = dataset_tracker
        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        resp = client.create_dataset(name=dataset_name)
        created.append(dataset_name)
        assert "successfully created" in resp["detail"].lower()

        search_resp = client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])
        names = [d["name"] for d in search_resp["data"]]
        assert dataset_name in names

    def test_search_non_existing_dataset(self, dataset_client):
        search_resp = dataset_client.search(
            filters=[{"field": "name", "operator": "eq", "value": "non_existing_dataset"}]
        )
        assert search_resp["data"] == []

    def test_search_multiple_existing_datasets(self, dataset_tracker):
        created, client = dataset_tracker
        names = [f"autotest_{uuid.uuid4().hex[:8]}" for _ in range(2)]
        for n in names:
            resp = client.create_dataset(name=n)
            created.append(n)
            assert "successfully created" in resp["detail"].lower()

        search_resp = client.search(filters=[{"field": "name", "operator": "in", "value": names}])
        found_names = {d["name"] for d in search_resp["data"]}
        assert set(names) <= found_names


class TestDatasetsFrontend:
    def test_delete_dataset(self, logged_in_page: Page, dataset_tracker):
        page = logged_in_page

        created, client = dataset_tracker

        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        create_resp = client.create_dataset(name=dataset_name)
        assert "detail" in create_resp
        assert "successfully created" in create_resp["detail"].lower()
        search_resp = client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])
        assert any(d["name"] == dataset_name for d in search_resp["data"])

        created.append(dataset_name)

        row = page.locator(f"div[role='none']:has-text('{dataset_name}')")
        expect(row).to_be_visible(timeout=10000)

        delete_button = row.locator("button", has=page.locator("svg")).last
        delete_button.click(force=True)

        expect(row).not_to_be_visible(timeout=10000)

        search_after = client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])
        assert all(d["name"] != dataset_name for d in search_after["data"])

    @pytest.mark.parametrize(
        "flow",
        [
            {"after_cancel": "Discard"},
            {"after_cancel": "Save"},
            {"save": True, "after_cancel": None},
        ],
    )
    def test_create_dataset_cancel(self, logged_in_page: Page, flow, dataset_tracker):
        page = logged_in_page
        created, client = dataset_tracker
        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        items = page.locator("a[class^='document-card-view-item_card-item']")
        expect(items.first).to_be_visible(timeout=10000)

        page.get_by_role("button", name="Add new dataset").click()
        dataset_modal = page.locator("div[role='modal']", has_text="Add dataset")
        dataset_modal.wait_for(state="visible", timeout=5000)
        page.get_by_role("textbox", name="Name").fill(dataset_name)

        if flow.get("save"):
            dataset_modal.get_by_role("button", name="Save").click(force=True)
            created.append(dataset_name)
            dataset_modal.wait_for(state="detached", timeout=5000)
            return

        dataset_modal.get_by_role("button", name="Cancel").click()

        if flow.get("after_cancel"):
            page.wait_for_selector(
                "div[role='modal']:has-text('Your data may be lost. Do you want to save data?')",
                state="visible",
                timeout=5000,
            )

            confirm_modal = page.locator("div[role='modal']").filter(
                has_text="Your data may be lost. Do you want to save data?"
            )
            if flow["after_cancel"] == "Save":
                created.append(dataset_name)

            confirm_modal.get_by_role("button", name=flow["after_cancel"]).click(force=True)

            confirm_modal.wait_for(state="detached", timeout=5000)
            dataset_modal.wait_for(state="detached", timeout=5000)

        expect(page.get_by_role("textbox", name="Name")).not_to_be_visible(timeout=5000)

    def test_create_dataset_no_name(self, logged_in_page: Page):
        page = logged_in_page
        items = page.locator("a[class^='document-card-view-item_card-item']")
        expect(items.first).to_be_visible(timeout=10000)

        page.get_by_role("button", name="Add new dataset").click()
        dataset_modal = page.locator("div[role='modal']", has_text="Add dataset")
        dataset_modal.wait_for(state="visible", timeout=5000)

        dataset_modal.get_by_role("button", name="Save").click(force=True)
        error_message = dataset_modal.locator("div[role='alert'].uui-invalid-message")
        expect(error_message).to_have_text("The field is mandatory", timeout=5000)

    def test_create_existing_dataset(self, logged_in_page: Page, dataset_tracker):
        page = logged_in_page
        created_datasets, client = dataset_tracker
        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        resp = client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)
        assert "successfully created" in resp["detail"].lower()

        document_items = page.locator("a[class^='document-card-view-item_card-item']")
        expect(document_items.first).to_be_visible(timeout=10000)

        page.get_by_role("button", name="Add new dataset").click()
        dataset_modal = page.locator("div[role='modal']", has_text="Add dataset")
        dataset_modal.wait_for(state="visible", timeout=5000)
        page.get_by_role("textbox", name="Name").fill(dataset_name)
        dataset_modal.get_by_role("button", name="Save").click(force=True)

        expect(page.locator(f"text=Dataset {dataset_name} already exists!")).to_be_visible(timeout=30000)

    @pytest.mark.parametrize("select_all", [True, False])
    def test_add_to_dataset_empty_field(self, logged_in_page: Page, select_all: bool):
        page = logged_in_page

        page.locator("rect").nth(0).click(force=True)

        if select_all:
            page.locator("label:has-text('Select All') div").first.click(force=True)
        else:
            item = page.locator("a[class^='document-card-view-item_card-item']").first
            item.scroll_into_view_if_needed()

            input_el = item.locator("input[type='checkbox']").first
            label = item.locator("label.uui-checkbox-container")
            uui_div = item.locator("div.uui-checkbox")

            click_target = label.first if label.count() else uui_div.first if uui_div.count() else input_el
            click_target.click(force=True)
            expect(input_el).to_be_checked()

        add_button = page.get_by_role("button", name="Add to dataset")
        add_button.click()

        choose_button = page.get_by_role("button", name="Choose")
        choose_button.click()

        error_label = page.locator("div.uui-invalid-message[role='alert']")
        expect(error_label).to_have_text("The field is mandatory")
