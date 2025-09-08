import pytest
from playwright.sync_api import Page, expect


class Locators:
    list_view_button = ("rect:nth-child(3)",)
    icon_view_button = ("rect:nth-child(6)",)


class TestIconViewSelection:
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
        expect(items.first).to_be_visible(timeout=5000)

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
