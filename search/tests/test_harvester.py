from typing import List
from unittest.mock import Mock

import pytest
from search.harvester import parse_json, start_harvester

from .override_app_dependency import TEST_TENANT

INDEX_NAME = TEST_TENANT

TOKENS = ["token_1", "token_2", "token_3"]

PAGE_OBJECTS = [
    {
        "id": "obj_id_1",
        "type": {"type": "some type"},
        "segmentation": "some segmentation",
        "original_annotation_id": 1,
        "links": ["link_1", "link_2", "link_3"],
        "category": "Header",
        "text": "Elasticsearch",
        "bbox": None,
        "tokens": TOKENS,
    },
    {
        "id": "obj_id_2",
        "type": {"type": "some type"},
        "segmentation": "some segmentation",
        "original_annotation_id": 1,
        "links": ["link_1", "link_2", "link_3"],
        "category": "Paragraph",
        "text": (
            "Elasticsearch is a search engine based on the Lucene library."
        ),
        "bbox": [20.2, 30.3, 145.5, 120.7],
        "tokens": None,
    },
    {
        "id": "obj_id_3",
        "type": {"type": "some type"},
        "segmentation": "some segmentation",
        "original_annotation_id": 1,
        "links": ["link_1", "link_2", "link_3"],
        "category": "Title",
        "text": "History",
        "bbox": None,
        "tokens": TOKENS,
    },
    {
        "id": "obj_id_4",
        "type": {"type": "some type"},
        "segmentation": "some segmentation",
        "original_annotation_id": 1,
        "links": ["link_1", "link_2", "link_3"],
        "category": "Footer",
        "text": "Cookie statements",
        "bbox": [100.0, 100.0, 300.0, 300.0],
        "tokens": None,
    },
    {
        "id": "obj_id_5",
        "type": {"type": "some type"},
        "segmentation": "some segmentation",
        "original_annotation_id": 1,
        "links": ["link_1", "link_2", "link_3"],
        "category": "Paragraph",
        "text": (
            "Shay Banon created the precursor to Elasticsearch, called "
            "Compass, in 2004."
        ),
        "bbox": None,  # for indexation of GeomObject with optional bbox
        "tokens": None,
    },
]

S3_PAGES = [
    {
        "id": "bf12fe3f26a73ef058c66547d278f59b8d76fe51",
        "page_num": 1,
        "size": [100, 200],
        "objs": PAGE_OBJECTS[0:2],
    },
    {
        "id": "bf12fe3f26a73ef058c66547d278f59b8d76fe52",
        "page_num": 1,
        "size": [100, 200],
        "objs": [PAGE_OBJECTS[2]],
    },
    {
        "id": "bf12fe3f26a73ef058c66547d278f59b8d76fe53",
        "page_num": 2,
        "size": [100, 200],
        "objs": [PAGE_OBJECTS[3]],
    },
    {
        "id": "bf12fe3f26a73ef058c66547d278f59b8d76fe56",
        "page_num": 2,
        "size": [100, 200],
        "objs": [PAGE_OBJECTS[4]],
    },
]

NO_TEXT_OBJ = {
    "id": "obj_id_6",
    "type": {"type": "some type"},
    "segmentation": "some segmentation",
    "links": ["link_1", "link_2", "link_3"],
    "category": "Paragraph",
    "data": {"some_data": "data"},
    "page_number": 2,
    "bbox": [0.0, 0.0, 0.0, 0.0],
}

EMPTY_TEXT_OBJ = {
    "id": "obj_id_7",
    "type": {"type": "some type"},
    "segmentation": "some segmentation",
    "links": ["link_1", "link_2", "link_3"],
    "category": "Paragraph",
    "text": "",
    "page_number": 2,
    "bbox": [0.0, 0.0, 0.0, 0.0],
}

S3_FAIL_PAGES = {
    "page_not_from_manifest": {
        "id": "bf12fe3f26a73ef058c66547d278f59b8d76fe57",
        "page_num": 1,
        "size": [100, 200],
        "objs": [
            {
                "id": "obj_id_1",
                "type": {"type": "some type"},
                "segmentation": "some segmentation",
                "links": ["link_1", "link_2", "link_3"],
                "category": "Header",
                "text": "I am not from any manifest.json!",
                "bbox": [10.0, 15.0, 300.0, 350.0],
            },
        ],
    },
    "page_no_geom_objs": {
        "id": "bf12fe3f26a73ef058c66547d278f59b8d76fe54",
        "page_num": 3,
        "size": [100, 200],
        "objs": [],
    },
    "page_wrong_geom_objs": {
        "id": "bf12fe3f26a73ef058c66547d278f59b8d76fe55",
        "page_num": 4,
        "size": [100, 200],
        "objs": [NO_TEXT_OBJ, EMPTY_TEXT_OBJ],
    },
}

MANIFESTS = [
    {
        "revision": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
        "user": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "pipeline": None,
        "date": "2021-10-20 09:30:22.038173",
        "job_id": 1,
        "pages": {"1": "bf12fe3f26a73ef058c66547d278f59b8d76fe51"},
        "validated": [1],
        "file": "files/path/path.pdf",
        "bucket": INDEX_NAME,
    },
    {
        "revision": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
        "user": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "pipeline": None,
        "date": "2021-10-20 09:30:22.038173",
        "job_id": 1,
        "pages": {
            "1": "bf12fe3f26a73ef058c66547d278f59b8d76fe52",
            "2": "bf12fe3f26a73ef058c66547d278f59b8d76fe53",
        },
        "validated": [1],
        "file": "files/path/path.pdf",
        "bucket": INDEX_NAME,
    },
    {
        "revision": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
        "user": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "pipeline": None,
        "date": "2021-10-20 09:30:22.038173",
        "job_id": 2,
        "pages": {
            "2": "bf12fe3f26a73ef058c66547d278f59b8d76fe56",
        },
        "validated": [],
        "file": "files/path/path.pdf",
        "bucket": INDEX_NAME,
    },
    {
        "revision": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
        "user": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "pipeline": None,
        "date": "2021-10-20 09:30:22.038173",
        "job_id": 1,
        "pages": {
            "3": "bf12fe3f26a73ef058c66547d278f59b8d76fe54",
            "4": "bf12fe3f26a73ef058c66547d278f59b8d76fe55",
        },
        "validated": [],
        "file": "files/path/path.pdf",
        "bucket": INDEX_NAME,
    },
    {
        "revision": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
        "user": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "pipeline": None,
        "date": "2021-10-20 09:30:22.038173",
        "job_id": 1,
        "pages": {},
        "validated": [],
        "file": "files/path/path.pdf",
        "bucket": INDEX_NAME,
    },
]

DOCS_IN_ES = [
    {
        "document_id": 1,
        "page_number": 1,
        "content": "Elasticsearch",
        "category": "Header",
        "bbox": None,
        "job_id": 1,
        "tokens": TOKENS,
    },
    {
        "document_id": 1,
        "page_number": 1,
        "content": "Elasticsearch is a search engine "
        "based on the Lucene library.",
        "category": "Paragraph",
        "bbox": [20.2, 30.3, 145.5, 120.7],
        "job_id": 1,
        "tokens": None,
    },
    {
        "document_id": 2,
        "page_number": 1,
        "content": "History",
        "category": "Title",
        "bbox": None,
        "job_id": 1,
        "tokens": TOKENS,
    },
    {
        "document_id": 2,
        "page_number": 2,
        "content": "Cookie statements",
        "category": "Footer",
        "bbox": [100.0, 100.0, 300.0, 300.0],
        "job_id": 1,
        "tokens": None,
    },
    {
        "document_id": 1,
        "page_number": 2,
        "content": "Shay Banon created the precursor to Elasticsearch, "
        "called Compass, in 2004.",
        "category": "Paragraph",
        "bbox": None,  # indexation of GeomObject with optional bbox
        "job_id": 2,
        "tokens": None,
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize(
    ["amount_of_uploads", "ids", "expected_result"],
    [
        (1, {"job_id": 1}, 4),
        (1, {"job_id": 1, "file_id": 1}, 2),
        (1, {"job_id": 2}, 1),
        (2, {"job_id": 1}, 4),
    ],
)
async def test_start_harvester_total_amount(
    monkeypatch,
    moto_s3,
    amount_of_uploads: int,
    ids: dict,
    expected_result: int,
    es,
):
    monkeypatch.setattr(
        "search.harvester.connect_s3", Mock(return_value=moto_s3)
    )
    monkeypatch.setattr("search.es.ES", es)
    for i in range(amount_of_uploads):
        await start_harvester(INDEX_NAME, **ids)
        await es.indices.refresh(index=INDEX_NAME)
    query_body = {"query": {"match_all": {}}}
    query_result = await es.search(index=INDEX_NAME, body=query_body)
    actual_result = query_result["hits"]["total"]["value"]
    assert actual_result == expected_result


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize(
    ["ids", "expected_result"],
    [
        ({"job_id": 1}, DOCS_IN_ES[:4]),
        ({"job_id": 1, "file_id": 1}, DOCS_IN_ES[:2]),
        ({"job_id": 1, "file_id": 2}, DOCS_IN_ES[2:4]),
        ({"job_id": 2}, [DOCS_IN_ES[4]]),
    ],
)
async def test_start_harvester_elastic_content(
    monkeypatch,
    moto_s3,
    es,
    ids,
    expected_result,
):
    monkeypatch.setattr(
        "search.harvester.connect_s3", Mock(return_value=moto_s3)
    )
    monkeypatch.setattr("search.es.ES", es)
    await start_harvester(INDEX_NAME, **ids)
    await es.indices.refresh(index=INDEX_NAME)
    actual_result = await get_all_es_docs(INDEX_NAME, es)
    assert actual_result == expected_result


@pytest.mark.asyncio
@pytest.mark.integration
async def test_start_harvester_no_text_objects(
    monkeypatch, moto_s3_fail_cases, es
):
    monkeypatch.setattr(
        "search.harvester.connect_s3",
        Mock(return_value=moto_s3_fail_cases),
    )
    monkeypatch.setattr("search.es.ES", es)
    await start_harvester(INDEX_NAME, 1)
    await es.indices.refresh(index=INDEX_NAME)
    query_body = {"query": {"match_all": {}}}
    query_result = await es.search(index=INDEX_NAME, body=query_body)
    docs_list = query_result["hits"]["hits"]
    actual_result = [doc["_source"] for doc in docs_list]
    assert actual_result == []


@pytest.mark.unittest
@pytest.mark.parametrize(
    (
        "text_piece_object",
        "job_id",
        "file_id",
        "page_num",
        "expected_result",
    ),
    [
        (
            S3_PAGES[0]["objs"],
            1,
            1,
            1,
            [
                {
                    "_index": INDEX_NAME,
                    "_source": {
                        "document_id": 1,
                        "page_number": 1,
                        "content": "Elasticsearch",
                        "category": "Header",
                        "bbox": None,
                        "job_id": 1,
                        "tokens": ["token_1", "token_2", "token_3"],
                    },
                },
                {
                    "_index": INDEX_NAME,
                    "_source": {
                        "document_id": 1,
                        "page_number": 1,
                        "content": "Elasticsearch is a search engine based "
                        "on the Lucene library.",
                        "category": "Paragraph",
                        "bbox": [20.2, 30.3, 145.5, 120.7],
                        "job_id": 1,
                        "tokens": None,
                    },
                },
            ],
        ),
        (
            S3_PAGES[1]["objs"],
            1,
            2,
            1,
            [
                {
                    "_index": INDEX_NAME,
                    "_source": {
                        "document_id": 2,
                        "page_number": 1,
                        "content": "History",
                        "category": "Title",
                        "bbox": None,
                        "job_id": 1,
                        "tokens": ["token_1", "token_2", "token_3"],
                    },
                }
            ],
        ),
        ({}, 1, 1, 1, []),
    ],
)
def test_parse_json(
    text_piece_object: list,
    job_id: int,
    file_id: str,
    page_num: str,
    expected_result: list,
):
    gen = parse_json(text_piece_object, job_id, file_id, page_num, INDEX_NAME)
    actual_result = []
    for i in range(len(text_piece_object)):
        actual_result.append(next(gen))
    assert actual_result == expected_result


async def get_all_es_docs(index: str, es) -> List[dict]:
    await es.indices.refresh(index=index)
    query_body = {"query": {"match_all": {}}}
    query_result = await es.search(index=INDEX_NAME, body=query_body)
    docs_list = query_result["hits"]["hits"]
    actual_result = [doc["_source"] for doc in docs_list]
    return actual_result


async def get_docs_ids(
    index: str, es, job_id: int = None, file_id: int = None
) -> List[str]:
    await es.indices.refresh(index=index)

    if job_id is None:
        query_body = None
    elif file_id is None:
        query_body = {"query": {"term": {"job_id": job_id}}}
    else:
        query_body = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"job_id": job_id}},
                        {"term": {"document_id": file_id}},
                    ]
                }
            }
        }
    query_result = await es.search(index=INDEX_NAME, body=query_body)
    docs_list = query_result["hits"]["hits"]
    actual_ids = {doc["_id"] for doc in docs_list}
    return actual_ids


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize(
    ["ids", "expected_result"],
    [
        ({"job_id": 1}, [DOCS_IN_ES[4]]),
        ({"job_id": 1, "file_id": 1}, DOCS_IN_ES[2:]),
        (
            {"job_id": 1, "file_id": 2},
            [DOCS_IN_ES[0], DOCS_IN_ES[1], DOCS_IN_ES[4]],
        ),
        ({"job_id": 2}, DOCS_IN_ES[:4]),
    ],
)
async def test_drop_es_documents(
    monkeypatch, dump_es_docs_empty_s3, ids, expected_result, es
):
    monkeypatch.setattr(
        "search.harvester.connect_s3",
        Mock(return_value=dump_es_docs_empty_s3),
    )
    monkeypatch.setattr("search.es.ES", es)
    docs_before_delete = await get_all_es_docs(INDEX_NAME, es)
    assert docs_before_delete == DOCS_IN_ES
    await start_harvester(INDEX_NAME, **ids)
    await es.indices.refresh(index=INDEX_NAME)
    docs_after_delete = await get_all_es_docs(INDEX_NAME, es)
    assert docs_after_delete == expected_result


def sort_es_docs(documents: List[dict]) -> List[dict]:
    return sorted(documents, key=lambda doc: doc["content"])


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize(
    ["ids"],
    [
        ({"job_id": 1},),
        ({"job_id": 1, "file_id": 1},),
        ({"job_id": 1, "file_id": 2},),
        ({"job_id": 2},),
    ],
)
async def test_harvester_updates_elastic_content(
    monkeypatch, dump_es_docs_moto_s3, ids, es
):
    monkeypatch.setattr(
        "search.harvester.connect_s3",
        Mock(return_value=dump_es_docs_moto_s3),
    )
    monkeypatch.setattr("search.es.ES", es)
    expected_documents = sort_es_docs(DOCS_IN_ES)
    docs_before_update = sort_es_docs(await get_all_es_docs(INDEX_NAME, es))
    old_docs_ids = await get_docs_ids(INDEX_NAME, es, **ids)
    old_other_docs_ids = await get_docs_ids(INDEX_NAME, es)
    old_other_docs_ids.difference_update(old_docs_ids)
    assert docs_before_update == expected_documents
    await start_harvester(INDEX_NAME, **ids)
    await es.indices.refresh(index=INDEX_NAME)
    docs_after_update = sort_es_docs(await get_all_es_docs(INDEX_NAME, es))
    new_docs_ids = await get_docs_ids(INDEX_NAME, es, **ids)
    new_other_docs_ids = await get_docs_ids(INDEX_NAME, es)
    new_other_docs_ids.difference_update(new_docs_ids)
    assert docs_after_update == expected_documents
    assert new_docs_ids != old_docs_ids
    assert new_other_docs_ids == old_other_docs_ids
