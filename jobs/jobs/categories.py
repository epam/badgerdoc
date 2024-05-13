import logging
from typing import List, Tuple

import jobs.models as models
import jobs.schemas as schemas
import jobs.utils as utils

logger = logging.getLogger(__name__)


async def prepare_for_update(
    current_job: models.CombinedJob,
    new_job: schemas.JobParamsToChange,
    current_tenant: str,
    jw_token: str,
) -> Tuple[List[str], List[schemas.CategoryLinkInput]]:
    logger.info("Prepare categories for update")
    new_categories_ids: List[str] = []
    new_categories_links: List[schemas.CategoryLinkInput] = []
    if new_job.categories:
        logger.info("Categories passed: %s", new_job.categories)
        new_categories_ids, new_categories_links = utils.get_categories_ids(
            new_job.categories
        )
        old_categories_ids = current_job.categories or []
        if set(new_categories_ids) != set(old_categories_ids):
            logger.warning(
                "This isn't expected to run here. "
                "It needs to be moved elsewhere."
            )
            await utils.delete_taxonomy_link(
                current_job.id, current_tenant, jw_token
            )
        else:
            new_categories_links = []

    if new_job.categories_append:
        logger.info(
            "Categories to append passed: %s", new_job.categories_append
        )
        new_categories_ids, new_categories_links = utils.get_categories_ids(
            new_job.categories_append
        )
        if new_categories_links:
            raise NotImplementedError(
                "The 'categories_append' field with links is not supported."
            )
        new_categories_ids = list(
            set(current_job.categories) | set(new_categories_ids)
        )

    logger.info(
        "Final categories: %s, %s", new_categories_ids, new_categories_links
    )
    return new_categories_ids, new_categories_links
