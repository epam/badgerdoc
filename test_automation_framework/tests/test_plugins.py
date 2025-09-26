from logging import getLogger
import uuid
from playwright.sync_api import expect
import pytest


logger = getLogger(__name__)


class TestPlugins:
    @pytest.mark.parametrize("iframe", [True, False])
    def test_create_and_delete_plugin(self, plugins_tracker, iframe):
        created, plugins_client = plugins_tracker
        unique_name = f"plugin_{uuid.uuid4().hex[:8]}"
        resp = plugins_client.create_plugin(
            name=unique_name,
            menu_name=unique_name,
            description="bar",
            version="1",
            url="http://what.com/what",
            is_iframe=iframe,
        )
        plugin_id = resp.id
        created.append(plugin_id)

        plugins = plugins_client.get_plugins()
        assert any(p.id == plugin_id for p in plugins)
        assert any(p.name == unique_name for p in plugins)

        plugins_client.delete_plugin(plugin_id)

        plugins = plugins_client.get_plugins()
        assert not any(p.id == plugin_id for p in plugins)

    def test_update_plugin(self, plugins_tracker):
        created, plugins_client = plugins_tracker
        unique_name = f"plugin_{uuid.uuid4().hex[:8]}"
        resp = plugins_client.create_plugin(
            name=unique_name,
            menu_name=unique_name,
            description="bar",
            version="1",
            url="http://what.com/what",
            is_iframe=True,
        )
        plugin_id = resp.id
        created.append(plugin_id)

        updated_payload = {
            "name": unique_name,
            "menu_name": unique_name,
            "description": "updated desc",
            "version": "1",
            "url": "http://what.com/what",
            "is_iframe": True,
        }
        update_resp = plugins_client.update_plugin(plugin_id, **updated_payload)
        assert update_resp.description == "updated desc"

        plugins = plugins_client.get_plugins()
        updated = next(p for p in plugins if p.id == plugin_id)
        assert updated.description == "updated desc"

    def test_view_plugins_from_settings(self, plugins_page, plugins_tracker):
        page = plugins_page
        created, plugins_client = plugins_tracker
        plugins = plugins_client.get_plugins()
        row_cells = page.locator("div[role='row'] div[role='cell']:first-child div div")
        frontend_names = [row_cells.nth(i).inner_text().strip() for i in range(row_cells.count())]
        api_names = [p.menu_name.strip() for p in plugins]
        assert set(frontend_names) == set(
            api_names
        ), f"Frontend plugins {frontend_names} do not match API plugins {api_names}"

    def test_sort_plugins_by_name(self, plugins_page, plugins_tracker):
        page = plugins_page
        row_cells = page.locator("div[role='row'] div[role='cell']:first-child div div")

        def get_frontend_names():
            return [row_cells.nth(i).inner_text().strip() for i in range(row_cells.count())]

        initial_names = get_frontend_names()
        assert initial_names, "No plugins loaded in frontend table"

        name_header = page.locator("div[role='columnheader'] >> text=Name")
        expect(name_header).to_be_visible()
        name_header.click()

        asc_names = get_frontend_names()
        assert asc_names == sorted(
            asc_names, key=lambda x: x.lower()
        ), f"Plugins not sorted ascending by name: {asc_names}"

        name_header.click()
        desc_names = get_frontend_names()
        assert desc_names == sorted(
            desc_names, key=lambda x: x.lower(), reverse=True
        ), f"Plugins not sorted descending by name: {desc_names}"

    @pytest.mark.parametrize("delete_action", ["confirm", "cancel"])
    @pytest.mark.parametrize("iframe", [False, True])
    def test_create_and_delete_plugin_via_ui(self, plugins_page, plugins_tracker, delete_action, iframe):
        created, plugins_client = plugins_tracker
        page = plugins_page

        plugin_name = f"plugin_{uuid.uuid4().hex[:6]}"
        menu_name = f"menu_{uuid.uuid4().hex[:6]}"
        description = "test plugin description"
        version = "1.0"
        url = "http://what.com/what"

        page.get_by_role("button", name="Add Plugin").click()
        page.get_by_role("textbox").nth(0).fill(plugin_name)
        page.get_by_role("textbox").nth(1).fill(menu_name)
        page.get_by_role("textbox").nth(2).fill(description)
        page.get_by_role("textbox").nth(3).fill(version)
        page.get_by_role("textbox", name="http://example.com/plugin").fill(url)

        if not iframe:
            page.locator("label", has_text="Is Iframe Plugin?").locator("div").nth(1).click()

        page.get_by_role("button", name="Save").click()

        row = page.get_by_role("row", name=menu_name)
        expect(row).to_be_visible(timeout=30000)

        plugins = plugins_client.get_plugins()
        plugin = next((p for p in plugins if p.name == plugin_name), None)
        created.append(plugin.id)
        assert plugin, f"Plugin {plugin_name} not found in API"
        assert plugin.is_iframe == iframe

        row.get_by_role("button").click()
        page.get_by_role("button", name=delete_action.capitalize()).click()

        if delete_action == "confirm":
            expect(page.get_by_role("row", name=menu_name)).not_to_be_visible(timeout=30000)
            plugins = plugins_client.get_plugins()
            assert all(plugin.id != p.id for p in plugins)
        else:
            expect(row).to_be_visible(timeout=30000)
            plugins = plugins_client.get_plugins()
            assert any(p.id == plugin.id for p in plugins)

    @pytest.mark.parametrize("missing_field", ["plugin_name", "menu_name", "version", "url"])
    def test_validate_mandatory_fields(self, plugins_page, missing_field, plugins_tracker):
        created, plugins_client = plugins_tracker
        page = plugins_page

        page.get_by_role("button", name="Add Plugin").click()

        plugin_name = f"plugin_{uuid.uuid4().hex[:6]}" if missing_field != "plugin_name" else ""
        menu_name = f"menu_{uuid.uuid4().hex[:6]}"
        version = "1.0"
        url = "http://what.com/what"

        if missing_field != "plugin_name":
            page.get_by_role("textbox").nth(0).fill(plugin_name)
        if missing_field != "menu_name":
            page.get_by_role("textbox").nth(1).fill(menu_name)
        if missing_field != "version":
            page.get_by_role("textbox").nth(3).fill(version)
        if missing_field != "url":
            page.get_by_role("textbox", name="http://example.com/plugin").fill(url)

        page.get_by_role("button", name="Save").click()

        if missing_field == "url":
            expect(page.get_by_text("Please enter a valid URL starting with http://")).to_be_visible()
            return

        plugins = plugins_client.get_plugins()
        plugin = next((p for p in plugins if p.name == plugin_name), None)
        assert plugin, f"Plugin {plugin_name} was not created (unexpected)"
        created.append(plugin.id)

        pytest.fail(f"Validation missing for {missing_field}, plugin {plugin.id} was created")
