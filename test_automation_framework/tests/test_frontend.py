import pytest
from playwright.sync_api import Page, expect


class Locators:
    list_view_button = ("rect:nth-child(3)",)
    icon_view_button = ("rect:nth-child(6)",)


class TestIconViewSelection:
    @pytest.mark.parametrize("rect_index", [0, 1])
    def test_select_all_views(self, logged_in_page, rect_index):
        page: Page = logged_in_page
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
    def test_view_switch(self, logged_in_page: Page, rect_index: str, file_locator: str):
        page = logged_in_page
        page.locator("rect").nth(rect_index).click(force=True)
        expect(page.locator(file_locator).first).to_be_visible()
