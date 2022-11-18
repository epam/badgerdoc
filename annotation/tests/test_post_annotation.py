import copy
import json
from hashlib import sha1
from typing import List
from unittest.mock import Mock, patch

import pytest
import responses
from fastapi import HTTPException
from fastapi.testclient import TestClient
from requests import RequestException
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.annotations import (
    MANIFEST,
    check_task_pages,
    construct_annotated_doc,
    create_manifest_json,
    get_pages_sha,
    row_to_dict,
)
from app.annotations.main import (
    check_docs_identity,
    upload_json_to_minio,
    upload_pages_to_minio,
)
from app.kafka_client import producers
from app.microservice_communication.assets_communication import (
    ASSETS_FILES_URL,
)
from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from app.models import (
    AnnotatedDoc,
    Category,
    File,
    Job,
    ManualAnnotationTask,
    User,
)
from app.schemas import (
    CategoryTypeSchema,
    DocForSaveSchema,
    JobTypeEnumSchema,
    PageSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from tests.consts import ANNOTATION_PATH
from tests.override_app_dependency import (
    TEST_HEADERS,
    TEST_TENANT,
    TEST_TOKEN,
    app,
)
from tests.test_tasks_crud_ud import construct_path

client = TestClient(app)

CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    ),
]
POST_ANNOTATION_ANNOTATOR = User(
    user_id="6ffab2dd-3605-46d4-98a1-2d20011e132d"
)
POST_ANNOTATION_VALIDATOR = User(
    user_id="6ffab2dd-3605-46d4-98a1-2d20011e132e"
)


FIRST_DATE = "2021-12-01T12:19:54.188831"
SECOND_DATE = "2021-12-02T09:19:54.188831"

POST_ANNOTATION_FILE_1 = File(
    **{
        "file_id": 1,
        "tenant": TEST_TENANT,
        "job_id": 1,
        "pages_number": 10,
    }
)
POST_ANNOTATION_FILE_2 = File(
    **{
        "file_id": 2,
        "tenant": TEST_TENANT,
        "job_id": 2,
        "pages_number": 10,
    }
)
POST_ANNOTATION_FILE_3 = File(
    **{
        "file_id": 3,
        "tenant": TEST_TENANT,
        "job_id": 4,
        "pages_number": 10,
    }
)

POST_ANNOTATION_JOB_1 = Job(
    **{
        "job_id": 1,
        "callback_url": "http://www.test.com/test1",
        "annotators": [POST_ANNOTATION_ANNOTATOR],
        "validation_type": ValidationSchema.cross,
        "files": [POST_ANNOTATION_FILE_1],
        "is_auto_distribution": False,
        "categories": CATEGORIES,
        "deadline": None,
        "tenant": TEST_TENANT,
        "job_type": JobTypeEnumSchema.ExtractionWithAnnotationJob,
    }
)
POST_ANNOTATION_JOB_2 = Job(
    **{
        "job_id": 2,
        "callback_url": "http://www.test.com/test1",
        "annotators": [POST_ANNOTATION_ANNOTATOR],
        "validation_type": ValidationSchema.cross,
        "files": [POST_ANNOTATION_FILE_2],
        "is_auto_distribution": False,
        "categories": CATEGORIES,
        "deadline": None,
        "tenant": TEST_TENANT,
    }
)

POST_ANNOTATION_VALIDATION_JOB = Job(
    **{
        "job_id": 3,
        "callback_url": "http://www.test.com/test1",
        "annotators": [POST_ANNOTATION_ANNOTATOR],
        "validators": [POST_ANNOTATION_VALIDATOR],
        "validation_type": ValidationSchema.hierarchical,
        "files": [POST_ANNOTATION_FILE_3],
        "is_auto_distribution": False,
        "categories": CATEGORIES,
        "deadline": None,
        "tenant": TEST_TENANT,
    }
)

POST_ANNOTATION_TASK_1 = {
    "id": 1,
    "file_id": POST_ANNOTATION_FILE_1.file_id,
    "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "job_id": POST_ANNOTATION_JOB_1.job_id,
    "user_id": POST_ANNOTATION_ANNOTATOR.user_id,
    "is_validation": True,
    "status": TaskStatusEnumSchema.in_progress,
    "deadline": None,
}
POST_ANNOTATION_PG_TASK_1 = ManualAnnotationTask(**POST_ANNOTATION_TASK_1)
POST_ANNOTATION_TASK_2 = {
    "id": 2,
    "file_id": POST_ANNOTATION_FILE_2.file_id,
    "pages": [1],
    "job_id": POST_ANNOTATION_JOB_2.job_id,
    "user_id": POST_ANNOTATION_ANNOTATOR.user_id,
    "is_validation": False,
    "status": TaskStatusEnumSchema.in_progress,
    "deadline": None,
}
POST_ANNOTATION_PG_TASK_2 = ManualAnnotationTask(**POST_ANNOTATION_TASK_2)

ANNOTATION_VALIDATION_TASKS = [
    {
        "id": 1,
        "file_id": POST_ANNOTATION_FILE_1.file_id,
        "pages": list(range(1, 11)),
        "job_id": POST_ANNOTATION_VALIDATION_JOB.job_id,
        "user_id": POST_ANNOTATION_ANNOTATOR.user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.pending,
        "deadline": None,
    },
    {
        "id": 2,
        "file_id": POST_ANNOTATION_FILE_1.file_id,
        "pages": list(range(1, 11)),
        "job_id": POST_ANNOTATION_VALIDATION_JOB.job_id,
        "user_id": POST_ANNOTATION_ANNOTATOR.user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.ready,
        "deadline": None,
    },
    {
        "id": 3,
        "file_id": POST_ANNOTATION_FILE_1.file_id,
        "pages": list(range(1, 11)),
        "job_id": POST_ANNOTATION_VALIDATION_JOB.job_id,
        "user_id": POST_ANNOTATION_ANNOTATOR.user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    },
    {
        "id": 4,
        "file_id": POST_ANNOTATION_FILE_1.file_id,
        "pages": list(range(1, 11)),
        "job_id": POST_ANNOTATION_VALIDATION_JOB.job_id,
        "user_id": POST_ANNOTATION_ANNOTATOR.user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.finished,
        "deadline": None,
    },
    {
        "id": 5,
        "file_id": POST_ANNOTATION_FILE_1.file_id,
        "pages": list(range(1, 11)),
        "job_id": POST_ANNOTATION_VALIDATION_JOB.job_id,
        "user_id": POST_ANNOTATION_VALIDATOR.user_id,
        "is_validation": True,
        "status": TaskStatusEnumSchema.ready,
        "deadline": None,
    },
    {
        "id": 6,
        "file_id": POST_ANNOTATION_FILE_1.file_id,
        "pages": list(range(1, 11)),
        "job_id": POST_ANNOTATION_VALIDATION_JOB.job_id,
        "user_id": POST_ANNOTATION_VALIDATOR.user_id,
        "is_validation": True,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    },
]
ANNOTATION_VALIDATION_TASKS_PG = [
    ManualAnnotationTask(**task) for task in ANNOTATION_VALIDATION_TASKS
]

TASK_ID = POST_ANNOTATION_TASK_1["id"]
PIPELINE_ID = 1
BAD_ID = "bad_id"
NOT_EXISTING_ID = 3

FIRST_PAGE = {
    "page_num": 1,
    "size": {"width": float(1), "height": float(1)},
    "objs": [
        {
            "id": 1,
            "type": "string",
            "segmentation": {"segment": "string"},
            "bbox": [float(1), float(1), float(1), float(1)],
            "tokens": None,
            "links": [{"category_id": 1, "to": 1, "page_num": 1}],
            "category": "1",
            "data": {},
        }
    ],
}
SHA_FIRST_PAGE = sha1(json.dumps(FIRST_PAGE).encode()).hexdigest()
POST_ANNOTATION_PG_DOC = AnnotatedDoc(
    revision="19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
    user=POST_ANNOTATION_ANNOTATOR.user_id,
    pipeline=None,
    date=FIRST_DATE,
    file_id=POST_ANNOTATION_FILE_1.file_id,
    job_id=POST_ANNOTATION_JOB_1.job_id,
    pages={"1": SHA_FIRST_PAGE},
    validated=[1],
    failed_validation_pages=[],
    tenant=POST_ANNOTATION_FILE_1.tenant,
    task_id=POST_ANNOTATION_PG_TASK_1.id,
)

S3_PATH = (
    f"annotation/{str(POST_ANNOTATION_PG_DOC.job_id)}/"
    f"{str(POST_ANNOTATION_PG_DOC.file_id)}"
)

ASSETS_RESPONSES = [
    {
        "pagination": {
            "page_num": 1,
            "page_size": 15,
            "min_pages_left": 1,
            "total": 3,
            "has_more": False,
        },
        "data": [
            {
                "id": POST_ANNOTATION_TASK_1["id"],
                "original_name": "some.pdf",
                "bucket": "merck",
                "size_in_bytes": 165887,
                "content_type": "image/png",
                "pages": 10,
                "last_modified": "2021-09-28T01:27:55",
                "path": f"files/{POST_ANNOTATION_TASK_1['id']}/"
                f"{POST_ANNOTATION_TASK_1['id']}.pdf",
                "datasets": [],
            }
        ],
    },
    {
        "pagination": {
            "page_num": 1,
            "page_size": 15,
            "min_pages_left": 1,
            "total": 3,
            "has_more": False,
        },
        "data": [],
    },
]

PAGES_AMOUNT = 10
PAGES_SCHEMA = [
    PageSchema(
        **{
            "page_num": i,
            "size": {"width": float(i), "height": float(i)},
            "objs": [
                {
                    "id": i,
                    "type": "string",
                    "segmentation": {"segment": "string"},
                    "bbox": [float(i), float(i), float(i), float(i)],
                    "tokens": None,
                    "links": [{"category_id": i, "to": i, "page_num": i}],
                    "category": f"{i}",
                    "data": {},
                }
            ],
        }
    )
    for i in range(1, PAGES_AMOUNT + 1)
]
PAGES = [page.dict() for page in PAGES_SCHEMA]

DIFF_FIRST_PAGE = copy.deepcopy(PAGES[1])
DIFF_FIRST_PAGE["page_num"] = 1
HASH_OF_DIFF_FIRST_PAGE = sha1(
    json.dumps(DIFF_FIRST_PAGE).encode()
).hexdigest()

DOC_FOR_FIRST_SAVE_BY_USER = {
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pages": [
        {
            "page_num": 1,
            "size": {"width": 0.0, "height": 0.0},
            "objs": [
                {
                    "id": 0,
                    "type": "string",
                    "segmentation": {"segment": "string"},
                    "bbox": [0.0, 0.0, 0.0, 0.0],
                    "tokens": None,
                    "links": [{"category_id": 0, "to": 0, "page_num": 1}],
                    "category": "0",
                    "data": {},
                }
            ],
        }
    ],
    "validated": [1],
    "failed_validation_pages": [],
}

DOC_WITH_BBOX_AND_TOKENS_FIELDS = copy.deepcopy(DOC_FOR_FIRST_SAVE_BY_USER)
DOC_WITH_BBOX_AND_TOKENS_FIELDS["pages"][0]["objs"][0]["tokens"] = [
    "token_1",
    "token_2",
]

DOC_WITHOUT_BBOX_AND_TOKENS = copy.deepcopy(DOC_FOR_FIRST_SAVE_BY_USER)
DOC_WITHOUT_BBOX_AND_TOKENS["pages"][0]["objs"][0]["bbox"] = None

DOC_FOR_SAVE_USER_ONLY_ANNOTATED = {
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pages": [
        {
            "page_num": 1,
            "size": {"width": 0.0, "height": 0.0},
            "objs": [
                {
                    "id": 0,
                    "type": "string",
                    "segmentation": {"segment": "string"},
                    "bbox": [0.0, 0.0, 0.0, 0.0],
                    "tokens": None,
                    "links": [{"category_id": 0, "to": 0, "page_num": 1}],
                    "category": "0",
                    "data": {},
                }
            ],
        }
    ],
}
DOC_FOR_SAVE_USER_ONLY_VALIDATED = {
    "user": POST_ANNOTATION_VALIDATOR.user_id,
    "validated": [1],
    "failed_validation_pages": [2],
}

DOC_FOR_FIRST_SAVE_BY_PIPELINE = {
    "pipeline": PIPELINE_ID,
    "pages": [
        {
            "page_num": 1,
            "size": {"width": 0.0, "height": 0.0},
            "objs": [
                {
                    "id": 0,
                    "type": "string",
                    "segmentation": {"segment": "string"},
                    "bbox": [0.0, 0.0, 0.0, 0.0],
                    "tokens": None,
                    "links": [{"category_id": 0, "to": 0, "page_num": 1}],
                    "category": "0",
                    "data": {},
                }
            ],
        }
    ],
}

DOC_FOR_SECOND_SAVE_BY_USER = {
    "base_revision": POST_ANNOTATION_PG_DOC.revision,
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pages": [
        {
            "page_num": 1,
            "size": {"width": 0.0, "height": 0.0},
            "objs": [
                {
                    "id": 0,
                    "type": "string",
                    "segmentation": {"segment": "string"},
                    "bbox": [0.0, 0.0, 0.0, 0.0],
                    "tokens": None,
                    "links": [{"category_id": 0, "to": 0, "page_num": 1}],
                    "category": "0",
                    "data": {},
                }
            ],
        }
    ],
    "validated": [1],
    "failed_validation_pages": [],
    "task_id": TASK_ID,
}
BASE_REVISION = DOC_FOR_SECOND_SAVE_BY_USER["base_revision"]


DOC_FOR_CHECK_MERGE_CONFLICT = {
    "base_revision": None,
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pipeline": None,
    "pages": [
        {
            "page_num": 2,
            "size": {"width": 0.0, "height": 0.0},
            "objs": [
                {
                    "id": 0,
                    "type": "string",
                    "segmentation": {"segment": "string"},
                    "bbox": [0.0, 0.0, 0.0, 0.0],
                    "tokens": None,
                    "links": [{"category_id": 0, "to": 0, "page_num": 1}],
                    "category": "0",
                    "data": {},
                }
            ],
        }
    ],
    "validated": [2, 3],
    "failed_validation_pages": [],
    "task_id": TASK_ID,
}

DOC_FOR_SAVE_WITH_MANY_PAGES = {
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pages": PAGES,
    "task_id": TASK_ID,
}

DOC_FOR_SAVE_WITHOUT_PAGES_AND_VALIDATED = {
    "base_revision": None,
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "task_id": TASK_ID,
}  # doc for test, when nothing to save

DOC_FOR_SAVE_NOT_TASK_PAGES = copy.deepcopy(DOC_FOR_FIRST_SAVE_BY_USER)
DOC_FOR_SAVE_NOT_TASK_PAGES["validated"] = [1, 100, 101]
DOC_FOR_SAVE_NOT_TASK_PAGES["failed"] = [102, 103]
DOC_FOR_SAVE_NOT_TASK_PAGES["pages"] = [
    {
        "page_num": 100,
        "size": {"width": 0.0, "height": 0.0},
        "objs": [
            {
                "id": 0,
                "type": "string",
                "segmentation": {"segment": "string"},
                "bbox": [0.0, 0.0, 0.0, 0.0],
                "tokens": None,
                "links": [{"category_id": 0, "to": 0, "page_num": 1}],
                "category": "0",
                "data": {},
            }
        ],
    }
]

ANNOTATED_DOC_FIRST = {
    "revision": sha1(
        json.dumps(DOC_FOR_FIRST_SAVE_BY_USER["pages"][0]).encode()
        + json.dumps(DOC_FOR_FIRST_SAVE_BY_USER["validated"]).encode()
        + json.dumps(
            DOC_FOR_FIRST_SAVE_BY_USER["failed_validation_pages"]
        ).encode()
    ).hexdigest(),
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pipeline": None,
    "file_id": POST_ANNOTATION_FILE_1.file_id,
    "job_id": POST_ANNOTATION_JOB_1.job_id,
    "pages": {
        "1": sha1(
            json.dumps(DOC_FOR_FIRST_SAVE_BY_USER["pages"][0]).encode()
        ).hexdigest()
    },
    "validated": DOC_FOR_FIRST_SAVE_BY_USER["validated"],
    "failed_validation_pages": [],
    "tenant": POST_ANNOTATION_PG_DOC.tenant,
    "task_id": POST_ANNOTATION_PG_TASK_1.id,
}
ANNOTATED_DOC_PIPELINE_FIRST = {
    "revision": sha1(
        json.dumps(DOC_FOR_FIRST_SAVE_BY_PIPELINE["pages"][0]).encode()
        + json.dumps(
            DOC_FOR_FIRST_SAVE_BY_PIPELINE.get("validated", [])
        ).encode()
        + json.dumps(
            DOC_FOR_FIRST_SAVE_BY_PIPELINE.get("failed_validation_pages", [])
        ).encode()
    ).hexdigest(),
    "user": None,
    "pipeline": PIPELINE_ID,
    "file_id": POST_ANNOTATION_FILE_1.file_id,
    "job_id": POST_ANNOTATION_JOB_1.job_id,
    "pages": {
        "1": sha1(
            json.dumps(DOC_FOR_FIRST_SAVE_BY_PIPELINE["pages"][0]).encode()
        ).hexdigest()
    },
    "tenant": POST_ANNOTATION_PG_DOC.tenant,
}

ANNOTATED_DOC_WITH_DIFFERENT_JOB_AND_FILE = copy.deepcopy(ANNOTATED_DOC_FIRST)
ANNOTATED_DOC_WITH_DIFFERENT_JOB_AND_FILE["file_id"] = POST_ANNOTATION_TASK_2[
    "file_id"
]
ANNOTATED_DOC_WITH_DIFFERENT_JOB_AND_FILE["job_id"] = POST_ANNOTATION_TASK_2[
    "job_id"
]
ANNOTATED_DOC_WITH_DIFFERENT_JOB_AND_FILE["task_id"] = POST_ANNOTATION_TASK_2[
    "id"
]

PAGES_SHA = {}
B_PAGES = b""
for page in PAGES_SCHEMA:
    b_page = json.dumps(page.dict()).encode()
    PAGES_SHA[str(page.page_num)] = sha1(b_page).hexdigest()
    B_PAGES += b_page

CONCATENATED_PAGES_SHA = sha1(
    B_PAGES + json.dumps([]).encode() + json.dumps([]).encode()
).hexdigest()

MANIFEST_IN_MINIO = {
    "revision": POST_ANNOTATION_PG_DOC.revision,
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pipeline": None,
    "job_id": POST_ANNOTATION_JOB_1.job_id,
    "file_id": POST_ANNOTATION_FILE_1.file_id,
    "pages": {"1": PAGES_SHA["1"]},
    "validated": [1],
    "failed_validation_pages": [],
    "bucket": "merck",
    "file": "path/to/file.pdf",
}

str_pgs_sha = {str(pg): PAGES_SHA[pg] for pg in PAGES_SHA}
ANNOTATED_DOC_WITH_MANY_PAGES = {
    "revision": CONCATENATED_PAGES_SHA,
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pipeline": None,
    "file_id": POST_ANNOTATION_FILE_1.file_id,
    "job_id": POST_ANNOTATION_JOB_1.job_id,
    "pages": str_pgs_sha,
    "validated": [],
    "failed_validation_pages": [],
    "tenant": POST_ANNOTATION_PG_DOC.tenant,
    "task_id": POST_ANNOTATION_PG_DOC.task_id,
}

ANNOTATED_DOC_WITH_BASE_REVISION = {
    "revision": sha1(
        DOC_FOR_SECOND_SAVE_BY_USER["base_revision"].encode()
        + json.dumps(DOC_FOR_SECOND_SAVE_BY_USER["pages"][0]).encode()
        + json.dumps(DOC_FOR_SECOND_SAVE_BY_USER["validated"]).encode()
        + json.dumps(
            DOC_FOR_SECOND_SAVE_BY_USER["failed_validation_pages"]
        ).encode()
    ).hexdigest(),
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pipeline": None,
    "file_id": POST_ANNOTATION_FILE_1.file_id,
    "job_id": POST_ANNOTATION_JOB_1.job_id,
    "pages": {
        "1": sha1(
            json.dumps(DOC_FOR_SECOND_SAVE_BY_USER["pages"][0]).encode()
        ).hexdigest()
    },
    "validated": [1],
    "failed_validation_pages": [],
    "tenant": POST_ANNOTATION_PG_DOC.tenant,
    "task_id": POST_ANNOTATION_PG_DOC.task_id,
}

ANNOTATED_DOC_WITH_BOTH_TOKENS_AND_BBOX = {
    "revision": sha1(
        json.dumps(DOC_WITH_BBOX_AND_TOKENS_FIELDS["pages"][0]).encode()
        + json.dumps(
            DOC_WITH_BBOX_AND_TOKENS_FIELDS.get("validated", [])
        ).encode()
        + json.dumps(
            DOC_WITH_BBOX_AND_TOKENS_FIELDS.get("failed_validation_pages", [])
        ).encode()
    ).hexdigest(),
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pipeline": None,
    "file_id": POST_ANNOTATION_FILE_1.file_id,
    "job_id": POST_ANNOTATION_JOB_1.job_id,
    "pages": {
        "1": sha1(
            json.dumps(DOC_WITH_BBOX_AND_TOKENS_FIELDS["pages"][0]).encode()
        ).hexdigest()
    },
    "validated": [1],
    "failed_validation_pages": [],
    "tenant": POST_ANNOTATION_PG_DOC.tenant,
    "task_id": POST_ANNOTATION_PG_DOC.task_id,
}

ANNOTATED_DOC_WITHOUT_BOTH_TOKENS_AND_BBOX = {
    "revision": sha1(
        json.dumps(DOC_WITHOUT_BBOX_AND_TOKENS["pages"][0]).encode()
        + json.dumps(DOC_WITHOUT_BBOX_AND_TOKENS.get("validated", [])).encode()
        + json.dumps(
            DOC_WITHOUT_BBOX_AND_TOKENS.get("failed_validation_pages", [])
        ).encode()
    ).hexdigest(),
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pipeline": None,
    "file_id": POST_ANNOTATION_FILE_1.file_id,
    "job_id": POST_ANNOTATION_JOB_1.job_id,
    "pages": {
        "1": sha1(
            json.dumps(DOC_WITHOUT_BBOX_AND_TOKENS["pages"][0]).encode()
        ).hexdigest()
    },
    "validated": [1],
    "failed_validation_pages": [],
    "tenant": POST_ANNOTATION_PG_DOC.tenant,
    "task_id": POST_ANNOTATION_PG_DOC.task_id,
}

ANNOTATED_DOCS_FOR_MANIFEST_CREATION = {
    "two_docs_1": (
        POST_ANNOTATION_PG_DOC,
        AnnotatedDoc(
            revision="20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
            user=POST_ANNOTATION_ANNOTATOR.user_id,
            pipeline=None,
            date=SECOND_DATE,
            file_id=POST_ANNOTATION_FILE_1.file_id,
            job_id=POST_ANNOTATION_JOB_1.job_id,
            pages={"2": PAGES_SHA["2"]},
            validated=[1, 2],
            failed_validation_pages=[],
            tenant=POST_ANNOTATION_PG_DOC.tenant,
        ),
    ),
    "two_docs_2": (
        POST_ANNOTATION_PG_DOC,
        AnnotatedDoc(
            revision="21fe52cce6a632c6eb09fdc5b3e1594f926eea69",
            user=POST_ANNOTATION_ANNOTATOR.user_id,
            pipeline=None,
            date=SECOND_DATE,
            file_id=POST_ANNOTATION_FILE_1.file_id,
            job_id=POST_ANNOTATION_JOB_1.job_id,
            pages={},
            validated=[],
            failed_validation_pages=[1],
            tenant=POST_ANNOTATION_PG_DOC.tenant,
        ),
    ),
    "two_docs_3": (
        POST_ANNOTATION_PG_DOC,
        AnnotatedDoc(
            revision="22fe52cce6a632c6eb09fdc5b3e1594f926eea69",
            user=POST_ANNOTATION_ANNOTATOR.user_id,
            pipeline=None,
            date=SECOND_DATE,
            file_id=POST_ANNOTATION_FILE_1.file_id,
            job_id=POST_ANNOTATION_JOB_1.job_id,
            pages={"2": PAGES_SHA["2"]},
            validated=[2],
            failed_validation_pages=[1],
            tenant=POST_ANNOTATION_PG_DOC.tenant,
        ),
    ),
    "two_docs_4": (
        AnnotatedDoc(
            revision="18fe52cce6a632c6eb09fdc5b3e1594f926eea69",
            user=POST_ANNOTATION_ANNOTATOR.user_id,
            pipeline=None,
            date=FIRST_DATE,
            file_id=POST_ANNOTATION_FILE_1.file_id,
            job_id=POST_ANNOTATION_JOB_1.job_id,
            pages={"1": PAGES_SHA["1"], "2": PAGES_SHA["2"]},
            validated=[1, 2],
            failed_validation_pages=[],
            tenant=POST_ANNOTATION_PG_DOC.tenant,
        ),
        AnnotatedDoc(
            revision="23fe52cce6a632c6eb09fdc5b3e1594f926eea69",
            user=POST_ANNOTATION_ANNOTATOR.user_id,
            pipeline=None,
            date=SECOND_DATE,
            file_id=POST_ANNOTATION_FILE_1.file_id,
            job_id=POST_ANNOTATION_JOB_1.job_id,
            pages={"3": PAGES_SHA["3"]},
            validated=[2, 3],
            failed_validation_pages=[1],
            tenant=POST_ANNOTATION_PG_DOC.tenant,
        ),
    ),
    "first_upload_without_pages_with_validated": AnnotatedDoc(
        revision=POST_ANNOTATION_PG_DOC.revision,
        user=POST_ANNOTATION_ANNOTATOR.user_id,
        file_id=POST_ANNOTATION_FILE_1.file_id,
        job_id=POST_ANNOTATION_JOB_1.job_id,
        pages={},
        validated=[1],
        failed_validation_pages=[],
        tenant="test-tenant",
    ),
    "first_upload_with_pages_without_validated_and_failed": (
        AnnotatedDoc(
            revision=POST_ANNOTATION_PG_DOC.revision,
            user=POST_ANNOTATION_ANNOTATOR.user_id,
            pipeline=None,
            file_id=POST_ANNOTATION_FILE_1.file_id,
            job_id=POST_ANNOTATION_JOB_1.job_id,
            pages=POST_ANNOTATION_PG_DOC.pages,
            validated=[],
            failed_validation_pages=[],
            tenant=POST_ANNOTATION_PG_DOC.tenant,
        ),  # from user
        AnnotatedDoc(
            revision=None,
            user=None,
            pipeline=PIPELINE_ID,
            file_id=POST_ANNOTATION_FILE_1.file_id,
            job_id=POST_ANNOTATION_JOB_1.job_id,
            pages=POST_ANNOTATION_PG_DOC.pages,
            validated=[],
            failed_validation_pages=[],
            tenant=POST_ANNOTATION_PG_DOC.tenant,
        ),  # from pipeline
    ),
    "same_pages": (
        POST_ANNOTATION_PG_DOC,
        AnnotatedDoc(
            revision="20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
            user=POST_ANNOTATION_ANNOTATOR.user_id,
            pipeline=None,
            date=SECOND_DATE,
            file_id=POST_ANNOTATION_FILE_1.file_id,
            job_id=POST_ANNOTATION_JOB_1.job_id,
            pages={"1": HASH_OF_DIFF_FIRST_PAGE},
            validated=[1],
            failed_validation_pages=[],
            tenant=POST_ANNOTATION_PG_DOC.tenant,
        ),
    ),
    "same_pages_not_validated": (
        AnnotatedDoc(
            revision="19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
            user=POST_ANNOTATION_ANNOTATOR.user_id,
            pipeline=None,
            date=SECOND_DATE,
            file_id=POST_ANNOTATION_FILE_1.file_id,
            job_id=POST_ANNOTATION_JOB_1.job_id,
            pages={"1": PAGES_SHA["1"]},
            validated=[],
            failed_validation_pages=[],
            tenant=POST_ANNOTATION_PG_DOC.tenant,
        ),
        AnnotatedDoc(
            revision="20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
            user=POST_ANNOTATION_ANNOTATOR.user_id,
            pipeline=None,
            date=SECOND_DATE,
            file_id=POST_ANNOTATION_FILE_1.file_id,
            job_id=POST_ANNOTATION_JOB_1.job_id,
            pages={"1": HASH_OF_DIFF_FIRST_PAGE},
            validated=[],
            failed_validation_pages=[],
            tenant=POST_ANNOTATION_PG_DOC.tenant,
        ),
    ),
}

ANNOTATED_DOC_WITH_MERGE_CONFLICT = {
    "revision": sha1(
        POST_ANNOTATION_PG_DOC.revision.encode()
        + json.dumps(DOC_FOR_CHECK_MERGE_CONFLICT["pages"][0]).encode()
        + json.dumps(DOC_FOR_CHECK_MERGE_CONFLICT["validated"]).encode()
        + json.dumps(
            DOC_FOR_CHECK_MERGE_CONFLICT["failed_validation_pages"]
        ).encode()
    ).hexdigest(),
    "user": POST_ANNOTATION_ANNOTATOR.user_id,
    "pipeline": None,
    "file_id": POST_ANNOTATION_FILE_1.file_id,
    "job_id": POST_ANNOTATION_JOB_1.job_id,
    "pages": {
        "1": POST_ANNOTATION_PG_DOC.pages["1"],
        "2": sha1(
            json.dumps(DOC_FOR_CHECK_MERGE_CONFLICT["pages"][0]).encode()
        ).hexdigest(),
    },
    "validated": [2, 3],
    "failed_validation_pages": [],
    "tenant": POST_ANNOTATION_PG_DOC.tenant,
    "task_id": POST_ANNOTATION_PG_DOC.task_id,
}


def get_objs_from_session(session: Session) -> List[dict]:
    """
    session.new will return identity set of objects added to session.
    """
    return [row_to_dict(obj) for obj in session.new]


def change_fields_type_to_list(annotated_doc: dict) -> dict:
    """
    While entity annotated doc is not committed to db,
    fields `validated` and `failed_validation_pages` may
    be assigned to sets, but after committing they become
    lists.
    Function `construct_annotated_doc` returns
    annotated_doc with `validated` and
    failed_validation_pages` assigned to sets.
    This helper function is needed to test,
    that between `annotated_doc`, that should be in db and
    `annotated_doc` returned by function `construct_annotated_doc`
    there is no difference except for these fields.
    """
    changed_doc = copy.deepcopy(annotated_doc)
    changed_doc["validated"] = list(changed_doc["validated"])
    changed_doc["failed_validation_pages"] = list(
        changed_doc["failed_validation_pages"]
    )
    return changed_doc


def delete_date_fields(annotated_docs: List[dict]) -> None:
    for doc in annotated_docs:
        del doc["date"]


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "task_id",
        "doc",
        "amount_of_uploads",
        "assets_response",
        "assets_status_code",
        "expected_code",
    ],
    [
        (
            TASK_ID,
            DOC_FOR_FIRST_SAVE_BY_USER,
            1,
            ASSETS_RESPONSES[0],
            200,
            201,
        ),  # trivial first save, file info was found
        (
            TASK_ID,
            DOC_FOR_FIRST_SAVE_BY_USER,
            1,
            ASSETS_RESPONSES[1],
            200,
            201,
        ),  # trivial first save, file info was not found
        (
            TASK_ID,
            DOC_FOR_FIRST_SAVE_BY_USER,
            2,
            ASSETS_RESPONSES[0],
            200,
            400,
        ),  # non mvp case for merge conflicts (in first upload first
        # rev created, in second upload with the same doc,
        # func checks, if latest rev was provided, finds out,
        # that provided rev is not latest,
        # checks if latest rev and given doc can be merged,
        # finds out that they have same changed pages
        # and throws an error)
        (
            TASK_ID,
            DOC_FOR_SECOND_SAVE_BY_USER,
            1,
            ASSETS_RESPONSES[0],
            200,
            404,
        ),  # annotated doc was not found
        (
            TASK_ID,
            {
                "pipeline": PIPELINE_ID,
                "pages": PAGES,
            },
            1,
            ASSETS_RESPONSES[0],
            200,
            400,
        ),  # user in provided doc should not be None, when saving
        # annotation by user
        (
            TASK_ID,
            {
                "user": "48987f26-e0e2-46b6-b674-adaf656fc3a3",
                "pages": PAGES,
            },
            1,
            ASSETS_RESPONSES[0],
            200,
            400,
        ),  # if user in provided doc does not match user_id
        # from task
        (
            NOT_EXISTING_ID,
            DOC_FOR_SECOND_SAVE_BY_USER,
            1,
            ASSETS_RESPONSES[0],
            200,
            404,
        ),  # task was not found
        (
            BAD_ID,
            DOC_FOR_SECOND_SAVE_BY_USER,
            1,
            ASSETS_RESPONSES[0],
            200,
            422,
        ),  # validation error
        (
            TASK_ID,
            {
                "pages": PAGES,
            },
            1,
            ASSETS_RESPONSES[0],
            200,
            422,
        ),  # fields user and pipeline should not be empty at the same time
        (
            TASK_ID,
            {
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": PIPELINE_ID,
                "pages": PAGES,
            },
            1,
            ASSETS_RESPONSES[0],
            200,
            422,
        ),  # fields user and pipeline should not be filled at the same time
        (
            TASK_ID,
            DOC_FOR_FIRST_SAVE_BY_USER,
            1,
            ASSETS_RESPONSES[0],
            404,
            500,
        ),  # if something wrong with assets
        (
            TASK_ID,
            DOC_FOR_SAVE_NOT_TASK_PAGES,
            1,
            ASSETS_RESPONSES[0],
            200,
            400,
        ),  # if pages for save do not belong to task
        (
            POST_ANNOTATION_TASK_2["id"],
            DOC_FOR_FIRST_SAVE_BY_USER,
            1,
            ASSETS_RESPONSES[0],
            200,
            400,
        ),  # trying to save validated or failed arrays
        # in annotation task
    ],
)
@patch("app.annotations.main.KafkaProducer", Mock)
@responses.activate
def test_post_annotation_by_user_status_codes(
    mock_minio_empty_bucket,
    prepare_db_for_post_annotation,
    task_id,
    doc,
    amount_of_uploads,
    assets_response,
    assets_status_code,
    expected_code,
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=assets_response,
        status=assets_status_code,
        headers=TEST_HEADERS,
    )

    for i in range(amount_of_uploads - 1):
        client.post(
            construct_path(ANNOTATION_PATH, task_id),
            headers={
                HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
                AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
            },
            json=doc,
        )
    with TestClient(app):
        mock_producer = producers["search_annotation"]
        mock_producer.send = Mock(return_value="any_message")
        response = client.post(
            construct_path(ANNOTATION_PATH, task_id),
            headers={
                HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
                AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
            },
            json=doc,
        )
    assert response.status_code == expected_code


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "doc",
        "assets_response",
        "assets_status_code",
        "expected_code",
    ],
    [
        (
            DOC_FOR_FIRST_SAVE_BY_PIPELINE,
            ASSETS_RESPONSES[0],
            200,
            201,
        ),  # basic save, file info was found
        (
            DOC_FOR_FIRST_SAVE_BY_PIPELINE,
            ASSETS_RESPONSES[1],
            200,
            201,
        ),  # basic save, file info was not found
        (
            DOC_FOR_SECOND_SAVE_BY_USER,
            ASSETS_RESPONSES[0],
            200,
            400,
        ),  # base_revision should be always None
        (
            {
                "pipeline": PIPELINE_ID,
            },
            ASSETS_RESPONSES[0],
            200,
            422,
        ),  # arrays pages, failed and validated
        # should not be empty at the same time
        (
            {
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pages": PAGES,
            },
            ASSETS_RESPONSES[0],
            200,
            400,
        ),  # pipeline in provided doc should not be None, when saving
        # annotation by pipeline
        (
            {
                "pages": PAGES,
            },
            ASSETS_RESPONSES[0],
            200,
            422,
        ),  # field user and pipeline should not be empty at the same time
        (
            {
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": PIPELINE_ID,
                "pages": PAGES,
            },
            ASSETS_RESPONSES[0],
            200,
            422,
        ),  # field user and pipeline should not be filled at the same time
        (
            DOC_FOR_FIRST_SAVE_BY_PIPELINE,
            ASSETS_RESPONSES[0],
            404,
            500,
        ),  # if something wrong with assets
    ],
)
@patch("app.annotations.main.KafkaProducer", Mock)
@responses.activate
def test_post_annotation_by_pipeline_status_codes(
    mock_minio_empty_bucket,
    prepare_db_for_post_annotation,
    doc,
    assets_response,
    assets_status_code,
    expected_code,
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=assets_response,
        status=assets_status_code,
        headers=TEST_HEADERS,
    )
    with TestClient(app):
        mock_producer = producers["search_annotation"]
        mock_producer.send = Mock(return_value="any_message")
        response = client.post(
            construct_path(
                ANNOTATION_PATH,
                f"{POST_ANNOTATION_PG_DOC.job_id}/"
                f"{POST_ANNOTATION_PG_DOC.file_id}",
            ),
            headers={
                HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
                AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
            },
            json=doc,
        )
    assert response.status_code == expected_code


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id", "doc", "len_pages", "expected_code"],
    [
        (
            TASK_ID,
            DOC_FOR_SECOND_SAVE_BY_USER,
            1,
            201,
        ),  # second revision, base revision from DOC_FOR_FIRST_SAVE_BY_USER
        (
            TASK_ID,
            DOC_FOR_CHECK_MERGE_CONFLICT,
            2,
            201,
        ),  # mvp case for merge conflicts
        (
            TASK_ID,
            DOC_FOR_SAVE_WITHOUT_PAGES_AND_VALIDATED,
            1,
            422,
        ),  # if pages, failed and validated not provided
    ],
)
@patch("app.annotations.main.KafkaProducer", Mock)
@responses.activate
def test_post_annotation_by_user_status_codes_with_existing_doc(
    mock_minio_empty_bucket,
    prepare_db_for_post_annotation_with_existing_doc,
    task_id,
    doc,
    len_pages,
    expected_code,
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSETS_RESPONSES[0],
        status=200,
        headers=TEST_HEADERS,
    )
    with TestClient(app):
        mock_producer = producers["search_annotation"]
        mock_producer.send = Mock(return_value="any_message")
        response = client.post(
            construct_path(ANNOTATION_PATH, task_id),
            headers={
                HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
                AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
            },
            json=doc,
        )

    if expected_code != 422:
        actual_len_pages = len(response.json()["pages"])
        assert actual_len_pages == len_pages
    assert response.status_code == expected_code


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["db_errors"],
    [
        (DBAPIError,),
        (SQLAlchemyError,),
    ],
    indirect=["db_errors"],
)
def test_post_annotation_by_user_db_exceptions(monkeypatch, db_errors):
    response = client.post(
        construct_path(ANNOTATION_PATH, TASK_ID),
        headers={
            HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
        json=DOC_FOR_SECOND_SAVE_BY_USER,
    )
    assert response.status_code == 500


@pytest.mark.integration
@responses.activate
def test_post_annotation_by_user_requests_exceptions(
    prepare_db_for_post_annotation,
):
    responses.add(
        responses.GET,
        ASSETS_FILES_URL,
        body=RequestException(),
        status=500,
        headers=TEST_HEADERS,
    )

    response = client.post(
        construct_path(ANNOTATION_PATH, TASK_ID),
        headers={
            HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
        json=DOC_FOR_FIRST_SAVE_BY_USER,
    )
    assert response.status_code == 500


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["pages", "base_revision", "validated", "failed", "expected_result"],
    [
        (
            PAGES_SCHEMA,
            BASE_REVISION,
            {1, 2, 3},
            set(),
            (
                PAGES_SHA,
                sha1(
                    BASE_REVISION.encode()
                    + B_PAGES
                    + json.dumps([1, 2, 3]).encode()
                    + json.dumps([]).encode()
                ).hexdigest(),
            ),
        ),  # first and second tests should have different revisions,
        # because they have different validated pages
        (
            PAGES_SCHEMA,
            BASE_REVISION,
            set(),
            set(),
            (
                PAGES_SHA,
                sha1(
                    BASE_REVISION.encode()
                    + B_PAGES
                    + json.dumps([]).encode()
                    + json.dumps([]).encode()
                ).hexdigest(),
            ),
        ),
        (
            PAGES_SCHEMA,
            None,
            {4, 4, 6},
            {7, 8},
            (
                PAGES_SHA,
                sha1(
                    b""
                    + B_PAGES
                    + json.dumps([4, 6]).encode()
                    + json.dumps([7, 8]).encode()
                ).hexdigest(),
            ),
        ),  # third and fourth tests should have same revisions,
        # because they have same base revision,
        # pages, failed and validated pages
        (
            PAGES_SCHEMA,
            None,
            {4, 6},
            {7, 8},
            (
                PAGES_SHA,
                sha1(
                    b""
                    + B_PAGES
                    + json.dumps([4, 6]).encode()
                    + json.dumps([7, 8]).encode()
                ).hexdigest(),
            ),
        ),
        (
            PAGES_SCHEMA,
            None,
            {4, 6},
            {10},
            (
                PAGES_SHA,
                sha1(
                    b""
                    + B_PAGES
                    + json.dumps([4, 6]).encode()
                    + json.dumps([10]).encode()
                ).hexdigest(),
            ),
        ),  # this test should have different from 3 and 4
        # tests revision, because it has different failed pages
        (
            [],
            BASE_REVISION,
            {1},
            {2},
            (
                {},
                sha1(
                    BASE_REVISION.encode()
                    + b""
                    + json.dumps([1]).encode()
                    + json.dumps([2]).encode()
                ).hexdigest(),
            ),
        ),  # this test`s revision should not match any other revision
    ],
)
def test_get_pages_sha(
    pages,
    base_revision,
    validated,
    failed,
    expected_result,
):
    actual_result = get_pages_sha(
        pages,
        base_revision,
        validated,
        failed,
    )

    assert actual_result == expected_result


@pytest.mark.unittest
def test_upload_json_to_minio(mock_minio_empty_bucket):
    s3_resource = mock_minio_empty_bucket

    path_to_object = "path/to/object.json"
    upload_json_to_minio(
        json.dumps(FIRST_PAGE), path_to_object, TEST_TENANT, s3_resource
    )

    s3_obj = s3_resource.Object(TEST_TENANT, path_to_object)
    actual_obj = json.loads(s3_obj.get()["Body"].read().decode("utf-8"))

    assert actual_obj == FIRST_PAGE


@pytest.mark.unittest
def test_upload_pages_to_minio(mock_minio_empty_bucket):
    s3_resource = mock_minio_empty_bucket

    upload_pages_to_minio(
        PAGES_SCHEMA, PAGES_SHA, S3_PATH, TEST_TENANT, s3_resource
    )

    for page_obj in s3_resource.Bucket(TEST_TENANT).objects.filter(
        Delimiter="/", Prefix=S3_PATH + "/"
    ):
        page_sha = page_obj.key.split("/")[-1].split(".")[0]
        page = json.loads(page_obj.get()["Body"].read().decode("utf-8"))
        assert page_sha == PAGES_SHA[str(page["page_num"])]
        assert page == PAGES_SCHEMA[page["page_num"] - 1].dict()


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["latest_doc", "new_doc", "expected_result"],
    [
        (
            # fields pages, validated and failed are equal
            # hence revisions are identical
            POST_ANNOTATION_PG_DOC,
            AnnotatedDoc(
                revision="29fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                user=POST_ANNOTATION_ANNOTATOR.user_id,
                pipeline=None,
                date=FIRST_DATE,
                file_id=POST_ANNOTATION_FILE_1.file_id,
                job_id=POST_ANNOTATION_JOB_1.job_id,
                pages={"1": SHA_FIRST_PAGE},
                validated={1},
                failed_validation_pages=set(),
                tenant=POST_ANNOTATION_FILE_1.tenant,
                task_id=POST_ANNOTATION_PG_TASK_1.id,
            ),
            True,
        ),
        (
            # if latest doc is None, revisions are not identical
            None,
            POST_ANNOTATION_PG_DOC,
            False,
        ),
        (
            # fields validated and failed are not equal
            # hence revisions are not identical
            POST_ANNOTATION_PG_DOC,
            AnnotatedDoc(
                revision="29fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                user=POST_ANNOTATION_ANNOTATOR.user_id,
                pipeline=None,
                date=FIRST_DATE,
                file_id=POST_ANNOTATION_FILE_1.file_id,
                job_id=POST_ANNOTATION_JOB_1.job_id,
                pages={"1": SHA_FIRST_PAGE},
                validated={1, 2},
                failed_validation_pages={3, 4},
                tenant=POST_ANNOTATION_FILE_1.tenant,
                task_id=POST_ANNOTATION_PG_TASK_1.id,
            ),
            False,
        ),
    ],
)
def test_check_docs_identity(latest_doc, new_doc, expected_result):
    actual_result = check_docs_identity(latest_doc, new_doc)
    assert actual_result == expected_result


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "annotated_doc",
        "s3_path_to_physical_file",
        "bucket_of_phys_file",
        "expected_manifest",
    ],
    [
        (
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get(
                "first_upload_without_pages_with_validated"
            ),
            "path/to/file",
            "bucket_of_phys_file",
            {
                "revision": POST_ANNOTATION_PG_DOC.revision,
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": None,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": {},
                "validated": [1],
                "failed_validation_pages": [],
            },
        ),  # revision contains only validated page.
        # manifest will be like:
        # pages: empty
        # validated: from revision
        # failed_validation_pages: empty
        (
            POST_ANNOTATION_PG_DOC,
            "path/to/file",
            "bucket-of-phys-file",
            {
                "revision": POST_ANNOTATION_PG_DOC.revision,
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": None,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": POST_ANNOTATION_PG_DOC.pages,
                "validated": POST_ANNOTATION_PG_DOC.validated,
                "failed_validation_pages": [],
            },
        ),  # revision contains pages, that have been validated
        # manifest will be like:
        # pages: from revision
        # validated: from revision
        # failed_validation_pages: empty
        (
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get(
                "first_upload_with_pages_without_validated_and_failed"
            )[0],
            "path/to/another/file",
            "another-bucket",
            {
                "revision": POST_ANNOTATION_PG_DOC.revision,
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": None,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": POST_ANNOTATION_PG_DOC.pages,
                "validated": [],
                "failed_validation_pages": [],
            },
        ),  # user's revision contains pages, that have not been validated yet
        # validated and failed_validations_pages are empty
        # manifest will be like:
        # pages: from revision
        # validated: empty
        # failed_validation_pages: empty
        (
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get(
                "first_upload_with_pages_without_validated_and_failed"
            )[1],
            "path/to/file",
            "bucket-of-phys-file",
            {
                "revision": None,
                "user": None,
                "pipeline": PIPELINE_ID,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": POST_ANNOTATION_PG_DOC.pages,
                "validated": [],
                "failed_validation_pages": [],
            },
        ),  # pipeline's revision contains pages, that have not been validated
        # manifest will be like:
        # pages: from revision
        # validated: empty
        # failed_validation_pages: empty
    ],
)
def test_create_manifest_json_first_upload(
    mock_minio_empty_bucket,
    annotated_doc,
    s3_path_to_physical_file,
    bucket_of_phys_file,
    expected_manifest,
    prepare_db_for_manifest_creation_with_one_record,
):
    """
    There is no manifest for these tests, which means, that it is first
    upload to minio.
    Annotated doc contains number and hash of uploaded page.
    """
    s3_resource = mock_minio_empty_bucket

    expected_manifest["bucket"] = bucket_of_phys_file
    expected_manifest["file"] = s3_path_to_physical_file
    create_manifest_json(
        annotated_doc,
        S3_PATH,
        s3_path_to_physical_file,
        bucket_of_phys_file,
        POST_ANNOTATION_PG_DOC.tenant,
        POST_ANNOTATION_JOB_1.job_id,
        POST_ANNOTATION_FILE_1.file_id,
        prepare_db_for_manifest_creation_with_one_record,
        s3_resource,
    )
    man_obj = s3_resource.Object(
        POST_ANNOTATION_PG_DOC.tenant, f"{S3_PATH}/{MANIFEST}"
    )
    actual_manifest = json.loads(man_obj.get()["Body"].read().decode("utf-8"))
    del actual_manifest["date"]
    assert actual_manifest == expected_manifest


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "prepare_db_for_manifest_creation_with_several_records",
        "annotated_doc",
        "s3_path_to_physical_file",
        "bucket_of_phys_file",
        "expected_manifest",
    ],
    [
        (
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get("two_docs_1"),
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get("two_docs_1")[1],
            "path/to/file",
            "bucket-of-phys-file",
            {
                "revision": "20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": None,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": {
                    "1": SHA_FIRST_PAGE,
                    "2": PAGES_SHA["2"],
                },
                "validated": [1, 2],
                "failed_validation_pages": [],
            },
        ),  # 1st and 2nd revisions contains pages, that have been validated
        # failed_validation array is empty
        # manifest will be like:
        # pages: both pages
        # validated: both pages
        # failed_validation_pages: empty
        (
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get("two_docs_2"),
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get("two_docs_2")[1],
            "path/to/another/file",
            "another-bucket",
            {
                "revision": "21fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": None,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": POST_ANNOTATION_PG_DOC.pages,
                "validated": [],
                "failed_validation_pages": [1],
            },
        ),  # 1st revision contains page "1" in 2nd revision no pages provided
        # but page from 1st revision in 2nd revision's failed list
        # so the manifest will be like:
        # pages: from 1st revision
        # validated : empty
        # failed_validation_pages: from 2nd revision
        (
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get("two_docs_3"),
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get("two_docs_3")[1],
            "path/to/another/file",
            "another_bucket",
            {
                "revision": "22fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": None,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": {**POST_ANNOTATION_PG_DOC.pages, "2": PAGES_SHA["2"]},
                "validated": [2],
                "failed_validation_pages": [1],
            },
        ),  # 1st revision contains page and validated page
        # 2nd contains page, validated page, but in failed_validation_pages
        # page from 1st revision presented,
        # so the manifest will be like:
        # pages: page "1" from 1st and "2" from 2nd revision
        # validated : from 2nd revision
        # failed_validation_pages: page from 1st revision
        (
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get("two_docs_4"),
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get("two_docs_4")[1],
            "path/to/another/file",
            "another-bucket",
            {
                "revision": "23fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": None,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": {
                    "1": PAGES_SHA["1"],
                    "2": PAGES_SHA["2"],
                    "3": PAGES_SHA["3"],
                },
                "validated": [2, 3],
                "failed_validation_pages": [1],
            },
        ),  # 1st revision contains two pages and validated page
        # 2nd contains page, validated page, and
        # page from 1st revision in failed_validation_pages array
        # so the manifest will be like:
        # pages: pages "1" and "2" from 1st revision, "3" - from 2nd
        # validated : from latest revision
        # failed_validation_pages: from latest revision
        (
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get("same_pages"),
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get("same_pages")[1],
            "path/to/another/file",
            "another-bucket",
            {
                "revision": "20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": None,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": {"1": HASH_OF_DIFF_FIRST_PAGE},
                "validated": [1],
                "failed_validation_pages": [],
            },
        ),  # 1st revision contains page and validated page
        # failed_validation_pages is empty
        # 2nd contains the same page, validated page and
        # failed_validation_pages is empty
        # so the manifest will be like:
        # pages: same page number but from latest revision
        # validated : from latest revision
        # failed_validation_pages: empty
        (
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get(
                "same_pages_not_validated"
            ),
            ANNOTATED_DOCS_FOR_MANIFEST_CREATION.get(
                "same_pages_not_validated"
            )[1],
            "path/to/another/file",
            "another-bucket",
            {
                "revision": "20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": None,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": {"1": HASH_OF_DIFF_FIRST_PAGE},
                "validated": [],
                "failed_validation_pages": [],
            },
        ),  # 1st revision contains page, that have not been validated yet
        # failed_validations_pages is empty
        # 2nd revision contains same page with different hash, but
        # haven't been validated and failed_validation_pages is empty
        # manifest will be like:
        # pages: same page number but from latest revision
        # validated: empty
        # failed_validation_pages: empty
    ],
    indirect=["prepare_db_for_manifest_creation_with_several_records"],
)
def test_create_manifest_json_with_annotated_docs_and_manifest_in_minio(
    minio_with_manifest,
    annotated_doc,
    s3_path_to_physical_file,
    bucket_of_phys_file,
    expected_manifest,
    prepare_db_for_manifest_creation_with_several_records,
):
    """
    One of pages is validated, so manifest contains validated page.
    There is manifest for these tests, which means, that it is not first
    upload to minio.
    """
    s3_resource = minio_with_manifest

    expected_manifest["bucket"] = bucket_of_phys_file
    expected_manifest["file"] = s3_path_to_physical_file

    create_manifest_json(
        annotated_doc,
        S3_PATH,
        s3_path_to_physical_file,
        bucket_of_phys_file,
        POST_ANNOTATION_PG_DOC.tenant,
        POST_ANNOTATION_JOB_1.job_id,
        POST_ANNOTATION_FILE_1.file_id,
        prepare_db_for_manifest_creation_with_several_records,
        s3_resource,
    )
    man_obj = s3_resource.Object(
        POST_ANNOTATION_PG_DOC.tenant, f"{S3_PATH}/{MANIFEST}"
    )
    actual_manifest = json.loads(man_obj.get()["Body"].read().decode("utf-8"))
    delete_date_fields([actual_manifest])
    assert actual_manifest == expected_manifest


@pytest.mark.integration
def test_create_manifest_json_date_field(
    prepare_db_for_manifest_creation_with_one_record, mock_minio_empty_bucket
):
    s3_resource = mock_minio_empty_bucket

    annotated_doc = row_to_dict(
        construct_annotated_doc(
            prepare_db_for_manifest_creation_with_one_record,
            POST_ANNOTATION_PG_TASK_1.user_id,
            None,
            POST_ANNOTATION_PG_TASK_1.job_id,
            POST_ANNOTATION_PG_TASK_1.file_id,
            DocForSaveSchema(**DOC_FOR_SECOND_SAVE_BY_USER),
            POST_ANNOTATION_PG_DOC.tenant,
            "path",
            "bucket",
            None,
            POST_ANNOTATION_PG_DOC.task_id,
            s3_resource,
        )
    )
    prepare_db_for_manifest_creation_with_one_record.commit()
    man_obj = s3_resource.Object(
        POST_ANNOTATION_PG_DOC.tenant, f"{S3_PATH}/{MANIFEST}"
    )
    actual_manifest = json.loads(man_obj.get()["Body"].read().decode("utf-8"))

    assert annotated_doc["date"]
    assert actual_manifest["date"]

    assert actual_manifest["date"] == annotated_doc["date"]


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "doc",
        "latest_doc",
        "is_latest",
        "expected_amount_of_docs",
        "expected_result",
    ],
    [
        (
            DocForSaveSchema(**DOC_FOR_SECOND_SAVE_BY_USER),
            None,
            True,
            2,
            ANNOTATED_DOC_WITH_BASE_REVISION,
        ),
        (
            DocForSaveSchema(**DOC_FOR_CHECK_MERGE_CONFLICT),
            POST_ANNOTATION_PG_DOC,
            False,
            2,
            ANNOTATED_DOC_WITH_MERGE_CONFLICT,
        ),
        (
            DocForSaveSchema(**DOC_WITH_BBOX_AND_TOKENS_FIELDS),
            None,
            True,
            2,
            ANNOTATED_DOC_WITH_BOTH_TOKENS_AND_BBOX,
        ),  # check construction of annotated doc
        # with both bbox and tokens fields
        (
            DocForSaveSchema(**DOC_WITHOUT_BBOX_AND_TOKENS),
            None,
            True,
            2,
            ANNOTATED_DOC_WITHOUT_BOTH_TOKENS_AND_BBOX,
        ),  # check construction of annotated doc
        # without bbox and tokens specified
        (
            DocForSaveSchema(
                user=POST_ANNOTATION_ANNOTATOR.user_id,
                pages=[FIRST_PAGE],
                validated=[1],
                failed_validation_pages=[],
            ),
            POST_ANNOTATION_PG_DOC,
            True,
            1,
            {
                "revision": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "user": POST_ANNOTATION_ANNOTATOR.user_id,
                "pipeline": None,
                "file_id": POST_ANNOTATION_FILE_1.file_id,
                "job_id": POST_ANNOTATION_JOB_1.job_id,
                "pages": {"1": SHA_FIRST_PAGE},
                "validated": [1],
                "failed_validation_pages": [],
                "tenant": POST_ANNOTATION_FILE_1.tenant,
                "task_id": POST_ANNOTATION_PG_TASK_1.id,
            },
        ),  # if new revision has same pages, validated and
        # failed validation arrays as latest revision,
        # new revision will not be created
        # and latest revision will be returned
    ],
)
def test_construct_annotated_doc(
    mock_minio_empty_bucket,
    prepare_db_for_post_annotation_with_existing_doc,
    doc,
    latest_doc,
    is_latest,
    expected_amount_of_docs,
    expected_result,
):
    """
    Checks, if annotated doc will be added to db session correctly,
    func will return created annotated doc and after commit
    field types will be changed to list.
    """
    db = prepare_db_for_post_annotation_with_existing_doc

    actual_doc = row_to_dict(
        construct_annotated_doc(
            db,
            POST_ANNOTATION_PG_TASK_1.user_id,
            None,
            POST_ANNOTATION_PG_TASK_1.job_id,
            POST_ANNOTATION_PG_TASK_1.file_id,
            doc,
            POST_ANNOTATION_PG_DOC.tenant,
            "path",
            "bucket",
            latest_doc,
            POST_ANNOTATION_PG_DOC.task_id,
            is_latest,
        )
    )
    formatted_actual_doc = change_fields_type_to_list(actual_doc)

    db.commit()

    doc_in_session_after_commit = get_objs_from_session(db)
    doc_in_db_after_commit = row_to_dict(
        db.query(AnnotatedDoc)
        .filter(AnnotatedDoc.revision == expected_result["revision"])
        .first()
    )
    amount_of_docs_after_commit = db.query(AnnotatedDoc).count()

    delete_date_fields(
        [actual_doc, doc_in_db_after_commit, formatted_actual_doc]
    )

    assert doc_in_session_after_commit == []
    assert doc_in_db_after_commit == expected_result
    assert amount_of_docs_after_commit == expected_amount_of_docs
    assert formatted_actual_doc == expected_result


@pytest.mark.integration
def test_construct_annotated_doc_different_jobs_and_files(
    mock_minio_empty_bucket,
    prepare_db_for_construct_doc,
):
    """
    Checks, if annotated doc will be added to db correctly
    and func will response correctly to fastapi (with annotated doc schema),
    Also checks, that pages in minio have correct path.
    """
    s3_resource = mock_minio_empty_bucket

    expected_result_1 = ANNOTATED_DOC_FIRST
    expected_result_2 = ANNOTATED_DOC_WITH_DIFFERENT_JOB_AND_FILE

    expected_path_1 = (
        f"annotation/{expected_result_1['job_id']}"
        f"/{expected_result_1['file_id']}.json"
    )
    expected_path_2 = (
        f"annotation/{expected_result_2['job_id']}"
        f"/{expected_result_2['file_id']}.json"
    )

    actual_doc_1 = row_to_dict(
        construct_annotated_doc(
            prepare_db_for_construct_doc,
            POST_ANNOTATION_PG_TASK_1.user_id,
            None,
            POST_ANNOTATION_PG_TASK_1.job_id,
            POST_ANNOTATION_PG_TASK_1.file_id,
            DocForSaveSchema(**DOC_FOR_FIRST_SAVE_BY_USER),
            POST_ANNOTATION_PG_DOC.tenant,
            "path",
            "bucket",
            None,
            POST_ANNOTATION_PG_TASK_1.id,
            True,
        )
    )
    formatted_actual_doc_1 = change_fields_type_to_list(actual_doc_1)

    actual_doc_2 = row_to_dict(
        construct_annotated_doc(
            prepare_db_for_construct_doc,
            POST_ANNOTATION_PG_TASK_2.user_id,
            None,
            POST_ANNOTATION_PG_TASK_2.job_id,
            POST_ANNOTATION_PG_TASK_2.file_id,
            DocForSaveSchema(**DOC_FOR_FIRST_SAVE_BY_USER),
            POST_ANNOTATION_PG_DOC.tenant,
            "another/path",
            "another-bucket",
            None,
            POST_ANNOTATION_PG_TASK_2.id,
            True,
        )
    )
    formatted_actual_doc_2 = change_fields_type_to_list(actual_doc_2)

    prepare_db_for_construct_doc.commit()

    doc_1_in_db = row_to_dict(
        prepare_db_for_construct_doc.query(AnnotatedDoc)
        .filter(
            AnnotatedDoc.revision == expected_result_1["revision"],
            AnnotatedDoc.job_id == expected_result_1["job_id"],
        )
        .first()
    )
    doc_2_in_db = row_to_dict(
        prepare_db_for_construct_doc.query(AnnotatedDoc)
        .filter(
            AnnotatedDoc.revision == expected_result_2["revision"],
            AnnotatedDoc.job_id == expected_result_2["job_id"],
        )
        .first()
    )

    delete_date_fields(
        [
            actual_doc_1,
            actual_doc_2,
            doc_1_in_db,
            doc_2_in_db,
            formatted_actual_doc_1,
            formatted_actual_doc_2,
        ]
    )

    obj_1 = s3_resource.Object(POST_ANNOTATION_PG_DOC.tenant, expected_path_1)
    obj_2 = s3_resource.Object(POST_ANNOTATION_PG_DOC.tenant, expected_path_2)

    assert obj_1.key == expected_path_1
    assert obj_2.key == expected_path_2

    assert doc_1_in_db == expected_result_1
    assert doc_2_in_db == expected_result_2

    assert formatted_actual_doc_1 == expected_result_1
    assert formatted_actual_doc_2 == expected_result_2


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id", "doc", "expected_result"],
    [
        (TASK_ID, DOC_FOR_FIRST_SAVE_BY_USER, ANNOTATED_DOC_FIRST),
        (TASK_ID, DOC_FOR_SAVE_WITH_MANY_PAGES, ANNOTATED_DOC_WITH_MANY_PAGES),
    ],
)
@patch("app.annotations.main.KafkaProducer", Mock)
@responses.activate
def test_post_annotation_by_user(
    mock_minio_empty_bucket,
    prepare_db_for_post_annotation,
    task_id,
    doc,
    expected_result,
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSETS_RESPONSES[0],
        status=200,
        headers=TEST_HEADERS,
    )
    with TestClient(app):
        mock_producer = producers["search_annotation"]
        mock_producer.send = Mock(return_value="any_message")
        actual_result = client.post(
            construct_path(ANNOTATION_PATH, task_id),
            headers={
                HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
                AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
            },
            json=doc,
        ).json()
    del actual_result["date"]
    assert actual_result == expected_result


@pytest.mark.integration
@patch("app.annotations.main.KafkaProducer", Mock)
@responses.activate
def test_post_annotation_by_pipeline(
    mock_minio_empty_bucket,
    prepare_db_for_post_annotation,
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSETS_RESPONSES[0],
        status=200,
        headers=TEST_HEADERS,
    )
    expected_result = copy.deepcopy(ANNOTATED_DOC_PIPELINE_FIRST)
    expected_result["validated"] = []
    expected_result["failed_validation_pages"] = []
    expected_result["task_id"] = None
    with TestClient(app):
        mock_producer = producers["search_annotation"]
        mock_producer.send = Mock(return_value="any_message")
        actual_result = client.post(
            construct_path(
                ANNOTATION_PATH,
                f"{POST_ANNOTATION_PG_DOC.job_id}/"
                f"{POST_ANNOTATION_PG_DOC.file_id}",
            ),
            headers={
                HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
                AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
            },
            json=DOC_FOR_FIRST_SAVE_BY_PIPELINE,
        ).json()
    del actual_result["date"]
    assert actual_result == expected_result


@pytest.mark.integration
@patch("app.annotations.main.KafkaProducer", Mock)
@responses.activate
def test_post_annotation_by_pipeline_two_eq_revs_in_a_row(
    mock_minio_empty_bucket, prepare_db_for_post_annotation
):
    db = prepare_db_for_post_annotation
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSETS_RESPONSES[0],
        status=200,
        headers=TEST_HEADERS,
    )
    with TestClient(app):
        mock_producer = producers["search_annotation"]
        mock_producer.send = Mock(return_value="any_message")
        two_docs_after_save = [
            client.post(
                construct_path(
                    ANNOTATION_PATH,
                    f"{POST_ANNOTATION_PG_DOC.job_id}/"
                    f"{POST_ANNOTATION_PG_DOC.file_id}",
                ),
                headers={
                    HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
                    AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
                },
                json=DOC_FOR_FIRST_SAVE_BY_PIPELINE,
            ).json()
            for _ in range(2)
        ]
        assert mock_producer.send.call_count == 1
    amount_of_docs_after_commit = db.query(AnnotatedDoc).count()
    assert two_docs_after_save[0] == two_docs_after_save[1]
    assert amount_of_docs_after_commit == 1


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task", "doc"],
    [
        (ANNOTATION_VALIDATION_TASKS[1], DOC_FOR_SAVE_USER_ONLY_ANNOTATED),
        (ANNOTATION_VALIDATION_TASKS[2], DOC_FOR_SAVE_USER_ONLY_ANNOTATED),
        (ANNOTATION_VALIDATION_TASKS[4], DOC_FOR_SAVE_USER_ONLY_VALIDATED),
        (ANNOTATION_VALIDATION_TASKS[5], DOC_FOR_SAVE_USER_ONLY_VALIDATED),
    ],
)
@patch("app.annotations.main.KafkaProducer", Mock)
@responses.activate
def test_post_user_annotation_change_task_statuses(
    mock_minio_empty_bucket,
    prepare_db_for_annotation_change_task_statuses,
    task,
    doc,
):
    session = prepare_db_for_annotation_change_task_statuses
    task_id = task["id"]
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSETS_RESPONSES[0],
        status=200,
        headers=TEST_HEADERS,
    )
    with TestClient(app):
        mock_producer = producers["search_annotation"]
        mock_producer.send = Mock(return_value="any_message")
        client.post(
            construct_path(ANNOTATION_PATH, task_id),
            headers={
                HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
                AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
            },
            json=doc,
        )
    db_task = session.query(ManualAnnotationTask).get(task_id)
    assert db_task.status == TaskStatusEnumSchema.in_progress


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task", "doc", "expected_message"],
    [
        (
            ANNOTATION_VALIDATION_TASKS[0],
            DOC_FOR_SAVE_USER_ONLY_ANNOTATED,
            "Job is not started yet",
        ),
        (
            ANNOTATION_VALIDATION_TASKS[3],
            DOC_FOR_SAVE_USER_ONLY_ANNOTATED,
            "Task is already finished",
        ),
    ],
)
@responses.activate
def test_post_user_annotation_wrong_task_statuses(
    mock_minio_empty_bucket,
    prepare_db_for_annotation_change_task_statuses,
    task,
    doc,
    expected_message,
):
    session = prepare_db_for_annotation_change_task_statuses
    task_id = task["id"]
    task_initial_status = task["status"]
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSETS_RESPONSES,
        status=200,
        headers=TEST_HEADERS,
    )
    annotation_response = client.post(
        construct_path(ANNOTATION_PATH, task_id),
        headers={
            HEADER_TENANT: POST_ANNOTATION_PG_DOC.tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
        json=doc,
    )
    assert annotation_response.status_code == 400
    assert expected_message in annotation_response.text
    db_task = session.query(ManualAnnotationTask).get(task_id)
    assert db_task.status == task_initial_status


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["pages", "validated", "failed", "task_pages"],
    [
        (
            [
                PageSchema(page_num=10, size={}, objs=[]),
            ],
            {1},
            {2},
            {1, 2, 3},
        ),
        (
            [
                PageSchema(page_num=1, size={}, objs=[]),
            ],
            {10},
            {2},
            {1, 2, 3},
        ),
        (
            [
                PageSchema(page_num=1, size={}, objs=[]),
            ],
            {1},
            {20},
            {1, 2, 3},
        ),
        (
            [
                PageSchema(page_num=100, size={}, objs=[]),
            ],
            {10},
            {20},
            {1, 2, 3},
        ),
    ],
)
def test_check_task_pages(pages, validated, failed, task_pages):
    with pytest.raises(HTTPException):
        check_task_pages(pages, validated, failed, task_pages)
