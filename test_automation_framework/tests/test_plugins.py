from logging import getLogger
import uuid

logger = getLogger(__name__)


class TestPlugins:
    def test_create_and_delete_plugin(self, plugins_tracker):
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
        plugin_id = resp["id"]
        created.append(plugin_id)

        plugins = plugins_client.get_plugins()
        assert any(p["id"] == plugin_id for p in plugins)
        assert any(p["name"] == unique_name for p in plugins)

        plugins_client.delete_plugin(plugin_id)

        plugins = plugins_client.get_plugins()
        assert not any(p["id"] == plugin_id for p in plugins)

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
        plugin_id = resp["id"]
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
        assert update_resp["description"] == "updated desc"

        plugins = plugins_client.get_plugins()
        updated = next(p for p in plugins if p["id"] == plugin_id)
        assert updated["description"] == "updated desc"
