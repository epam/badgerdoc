from unittest.mock import patch

import pytest

import jobs.categories as categories
import jobs.models as models
import jobs.schemas as schemas


class TestPrepareForUpdate:
    @pytest.mark.asyncio
    async def test_categories_field(
        self,
        combined_job_for_update: models.CombinedJob,
        categories_change_request: schemas.JobParamsToChange,
    ) -> None:
        with patch("jobs.categories.utils.delete_taxonomy_link") as txn_call:
            cats, _ = await categories.prepare_for_update(
                combined_job_for_update,
                categories_change_request,
                current_tenant="test",
                jw_token="test",
            )
            assert cats == categories_change_request.categories
            if categories_change_request.categories and set(
                categories_change_request.categories
            ) != set(combined_job_for_update.categories):
                txn_call.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_categories_append_field(
        self,
        combined_job_for_update: models.CombinedJob,
        categories_append_request: schemas.JobParamsToChange,
    ) -> None:
        cats, _ = await categories.prepare_for_update(
            combined_job_for_update,
            categories_append_request,
            current_tenant="test",
            jw_token="test",
        )
        if categories_append_request.categories_append:
            assert cats == list(
                set(categories_append_request.categories_append)
                | set(combined_job_for_update.categories)
            )
        else:
            assert not cats
