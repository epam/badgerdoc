import pytest
from playwright.sync_api import Page, expect


class TestIconViewSelection:
    @pytest.mark.parametrize(
        "view_selector",
        [
            "rect:nth-child(3)",  # list view button
            "path:nth-child(6)",  # icon view button
        ],
    )
    def test_select_all_views(self, logged_in_page, view_selector):
        page: Page = logged_in_page
        page.locator(view_selector).click()
        select_all = page.locator("label:has-text('Select All') div").first
        select_all.click()
        file_inputs = page.locator("div.uui-checkbox > input[type='checkbox']")
        for i in range(file_inputs.count()):
            expect(file_inputs.nth(i)).to_be_checked()
        select_all = page.locator("label:has-text('selected') div").first
        select_all.click()
        file_inputs = page.locator("div.uui-checkbox > input[type='checkbox']")
        for i in range(file_inputs.count()):
            expect(file_inputs.nth(i)).not_to_be_checked()
