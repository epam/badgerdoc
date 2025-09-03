from logging import getLogger
import uuid

import pytest

logger = getLogger(__name__)


class TestCategories:
    @pytest.mark.skip(reason="Creation works, but deletion not implemented, will be cluttered by multiple runs")
    def test_create_and_delete_category(self, auth_token, settings, tenant, categories_client):
        access_token, _ = auth_token

        unique_id = f"test_cat_{uuid.uuid4().hex[:6]}"
        created = categories_client.create_category(category_id=unique_id, name=unique_id, parent="example")
        assert created.id == unique_id
        search_result = categories_client.search_categories(page_size=100)
        ids = [c.id for c in search_result.data]
        assert unique_id in ids, f"Category {unique_id} not found after creation"

        deleted = categories_client.delete_category(unique_id)
        assert deleted.get("detail") or deleted.get("status") or "success" in str(deleted).lower()
        search_after_delete = categories_client.search_categories(page_size=100)
        ids_after = [c.id for c in search_after_delete.data]
        assert unique_id not in ids_after, f"Category {unique_id} still present after deletion"
