from logging import getLogger
from playwright.sync_api import Page, expect


logger = getLogger(__name__)


class TestTasksFrontend:
    def test_tasks_scroll(self, tasks_page: Page):
        page = tasks_page

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

    def test_tasks_pagination_by_page_number(self, tasks_page: Page):
        page = tasks_page
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

    def test_tasks_pagination_by_arrows(self, tasks_page: Page):
        page = tasks_page

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

    def test_tasks_show_on_page(self, tasks_page: Page):
        page = tasks_page

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
            page.wait_for_timeout(1000)
            page.wait_for_function(
                """(expected) => {
                    const rows = document.querySelectorAll("div[role='row']:not(.uui-table-header-row)");
                    return rows.length <= expected;
                }""",
                arg=int(value),
                timeout=5000,
            )
            count = rows.count()
            assert count <= int(value), f"Expected at most {value} rows, got {count}"
