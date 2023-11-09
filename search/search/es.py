from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from opensearchpy import AsyncOpenSearch
from opensearchpy.exceptions import NotFoundError, RequestError
from search.embeddings.embeddings  import get_embeduse_embeddings
from search.embeddings.embeddings  import get_qa_embeduse_embeddings
from search.config import settings

INDEX_SETTINGS = {
    "settings": {
        "index": {
            "knn": True
        }
    },
    "mappings": {
        "properties": {
            "category": {
                "type": "keyword",
            },
            "content": {
                "type": "text",
            },
            "document_id": {
                "type": "keyword",
            },
            "page_number": {
                "type": "integer",
            },
            "job_id": {
                "type": "keyword",
            },
            "embedding": {
              "type": "knn_vector",
              "dimension": 512
            },
            "resp_embedding": {
              "type": "knn_vector",
              "dimension": 512
            }
        },
    }
}

ES: AsyncOpenSearch = AsyncOpenSearch(
    hosts=settings.es_host, port=settings.es_port
)


class NoSuchTenant(Exception):
    def __init__(self, message):
        self.message = message


class NoCategory(NoSuchTenant):
    pass


async def prepare_index(
    es_instance: AsyncOpenSearch, index_name: str
) -> None:
    if not await es_instance.indices.exists(index=index_name):
        try:
            await es_instance.indices.create(
                index=index_name, body=INDEX_SETTINGS
            )
        except RequestError as exc:
            if exc.error == "resource_already_exists_exception":
                pass
            else:
                raise exc


async def search_v2(
    es_instance: AsyncOpenSearch,
    index_name: str,
    es_query: Dict[str, Any],
) -> Dict[str, Any]:
    es_response = None
    try:
        es_response = await es_instance.search(index=index_name, body=es_query)
    except NotFoundError as exc:
        if exc.error == "index_not_found_exception":
            raise NoSuchTenant(f"Index for tenant {index_name} doesn't exist")
    return es_response


async def search(
    es_instance: AsyncOpenSearch,
    index_name: str,
    search_params: dict,
    pagination_page_size: int,
    pagination_start_page: int,
    token: str,
) -> dict:
    query = await build_query(
        pagination_start_page,
        pagination_page_size,
        search_params,
        index_name,
        token,
    )
    es_response = None
    try:
        es_response = await es_instance.search(index=index_name, body=query)
    except NotFoundError as exc:
        if exc.error == "index_not_found_exception":
            raise NoSuchTenant(f"Index for tenant {index_name} doesn't exist")
    total_objects = es_response["hits"]["total"]["value"]
    return {
        "current_page": pagination_start_page,
        "page_size": pagination_page_size,
        "total_objects": total_objects,
        "text_pieces": [x["_source"] for x in es_response["hits"]["hits"]],
    }


async def build_query(
    pagination_start_page: int,
    pagination_page_size: int,
    search_parameters: dict,
    tenant: str,
    token: str,
) -> dict:
    """Return query for search in ES index. If no search_parameters provided -
    make query to search all TextPieces with "match_all". Otherwise parameters
    will be located in "bool" subquery: "content" for full-text search in
    "must" -> "match_all"; list with provided "category" id and ids of child
    categories (requested from "annotation" service) - in "filter" -> "terms".
    All remaining fields will be located in "filter" -> "term" subqueries."""
    query = {
        "from": (pagination_start_page - 1) * pagination_page_size,
        "size": pagination_page_size,
        "query": {},
    }
    if not search_parameters:
        query["query"]["match_all"] = {}
        return query
    query["query"]["bool"] = {}
    embed_fields = {"sentence": "embedding", "question": "resp_embedding"}
    is_embed = [k for k in search_parameters.keys() if k in embed_fields]
    if len(is_embed) > 0:
        query_str = search_parameters.pop(is_embed[0])
        embed_field = embed_fields[is_embed[0]]
        if "sentence" == is_embed[0]:
            boost_by_txt_emb = get_embeduse_embeddings([query_str], settings.embed_url)[0]
        else:
            boost_by_txt_emb = get_qa_embeduse_embeddings(query_str, settings.qa_embed_question_url)
        knn_subquery = {
            embed_field: {
                'vector': boost_by_txt_emb,
                'k': 512
            }
        }
        query["query"]["bool"]["must"] = [
            {
                "knn": knn_subquery
            }
        ]
    if "question" in search_parameters:
        query_str = search_parameters.pop("question")
        boost_by_txt_emb = get_embeduse_embeddings([query_str], settings.embed_url)[0]
        knn_subquery = {
            'embedding': {
                'vector': boost_by_txt_emb,
                'k': 512
            }
        }
        query["query"]["bool"]["must"] = [
            {
                "knn": knn_subquery
            }
        ]
    elif "content" in search_parameters:
        query["query"]["bool"]["must"] = [
            {
                "match": {"content": search_parameters.pop("content")}
            }
        ]
    if search_parameters:
        query["query"]["bool"]["filter"] = []
    if "category" in search_parameters:
        category_id = search_parameters.pop("category")
        categories_ids = await add_child_categories(category_id, tenant, token)
        terms_filter = {"terms": {"category": categories_ids}}
        query["query"]["bool"]["filter"].append(terms_filter)
    for parameter, value in search_parameters.items():
        query["query"]["bool"]["filter"].append(
            {"term": {parameter: {"value": value}}}
        )
    #print(query)
    return query


async def add_child_categories(
    category_id: str, tenant: str, token: str
) -> List[str]:
    """Helper function which makes GET request into "annotation" service
    endpoint and returns list of provided category_id with ids of all
    subcategories from endpoint's response.
    """
    child_category_url = (
        f"{settings.annotation_categories_url}/{category_id}/child"
    )
    header = {"X-Current-Tenant": tenant, "Authorization": f"Bearer {token}"}

    try:
        status, result = await fetch("GET", child_category_url, headers=header)
        categories_ids = (
            [category["id"] for category in result] + [category_id]
            if status == 200
            else [category_id]
        )
    except aiohttp.ContentTypeError as err:
        raise NoCategory(
            f"Can't get subcategories for {category_id} due to error {err}"
        )
    except aiohttp.ClientError as err:
        raise NoCategory(
            f"Can't get subcategories for {category_id} due to error {err}"
        )
    return categories_ids


async def fetch(
    method: str,
    url: str,
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    async with aiohttp.request(
        method=method, url=url, json=body, headers=headers
    ) as resp:
        status = resp.status
        json = await resp.json()
        return status, json
