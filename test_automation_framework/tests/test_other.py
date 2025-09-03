from logging import getLogger

logger = getLogger(__name__)


class TestMenu:
    def test_menu(self, menu_client):
        menu = menu_client.get_menu()
        assert isinstance(menu, list)
        assert menu
        required_keys = {"name", "badgerdoc_path", "is_external", "is_iframe", "url", "children"}
        for item in menu:
            assert required_keys <= item.keys()
        first_item = menu[0]
        assert isinstance(first_item["name"], str)
        assert isinstance(first_item["badgerdoc_path"], str)
        assert isinstance(first_item["is_external"], bool)
        assert isinstance(first_item["children"], (list, type(None)))
        expected_names = {"Documents", "My Tasks", "Jobs", "Settings"}
        actual_names = {item["name"] for item in menu}
        assert expected_names <= actual_names
        settings_item = next(i for i in menu if i["name"] == "Settings")
        assert isinstance(settings_item["children"], list)
        assert any(child["name"] == "Keycloak" for child in settings_item["children"])
