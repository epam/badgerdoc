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


class TestControls:
    def test_scroll_documents(self, logged_in_page: Page):
        page = logged_in_page

        last_doc = page.locator('a[class*="document-card-view-item_card-item"]').last
        last_doc.scroll_into_view_if_needed()
        expect(last_doc).to_be_visible()

        first_doc = page.locator('a[class*="document-card-view-item_card-item"]').first
        first_doc.scroll_into_view_if_needed()
        expect(first_doc).to_be_visible()

    def test_pagination_by_page_number(self, logged_in_page: Page):
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

    def test_pagination_by_arrows(self, logged_in_page: Page):
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

    def test_show_on_page(self, logged_in_page: Page):
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
            print(f"Expected at most {value} cards, got {count}")
            assert count <= int(value), f"Expected at most {value} cards, got {count}"
