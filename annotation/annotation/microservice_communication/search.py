"""
Example of response for files:
    {
       "pagination":{
          "page_num":1,
          "page_size":15,
          "min_pages_left":1,
          "total":3,
          "has_more":false
       },
       "data":[
          {
             "id":1,
             "original_name":"A17_FlightPlan.pdf",
             "bucket":"tenant1",
             "size_in_bytes":20702285,
             "extension":".pdf",
             "content_type":"application/pdf",
             "pages":618,
             "last_modified":"2021-11-22T04:26:42.792752",
             "status":"uploaded",
             "path":"files/1/1.pdf",
             "datasets":[
                "string"
             ]
          },
          {...}
       ]
    }

Example of response for datasets:
    {
       "pagination":{
          "page_num":1,
          "page_size":15,
          "min_pages_left":1,
          "total":3,
          "has_more":false
       },
       "data":[
          {
             "id":1,
             "name":"string",
             "count":3,
             "created":"2021-11-22T04:26:16.006341"
          },
          {...}
       ]
    }

Example of response for jobs:
    {
        "pagination": {
            "page_num": 1,
            "page_size": 15,
            "min_pages_left": 1,
            "total": 1,
            "has_more": false
        },
        "data": [
            {
            "id": 4,
            "name": "AnnotationJob_draft_test",
            "status": "Pending",
            "files": [
                4
            ],
            "datasets": [],
            "creation_datetime": "2021-11-15T15:30:20.870707",
            "type": "AnnotationJob",
            "mode": "Manual",
            "annotators": [
                "02336646-f5d0-4670-b111-c140a3ad58b5",
                "ca993bc3-f128-4d1d-81ba-e2b117004e20",
                "5700519e-2320-4610-b329-3f592565b700"
            ],
            "categories": [
                1,
                2,
                3
            ],
            "is_auto_distribution": false,
            "deadline": "2022-01-06T17:28:49.312000",
            "validation_type": "cross"
            }
        ]
    }

"""
import os
from typing import Dict, List

import requests
from fastapi import Header, HTTPException
from requests.exceptions import ConnectionError, RequestException, Timeout

from annotation.annotations import row_to_dict
from annotation.models import ManualAnnotationTask
from annotation.schemas import ExpandedManualAnnotationTaskSchema

PAGE_SIZE = 100  # max page size in assets
HEADER_TENANT = "X-Current-Tenant"
AUTHORIZATION = "Authorization"
BEARER = "Bearer"
X_CURRENT_TENANT_HEADER = Header(..., alias=HEADER_TENANT, example="test")
USERS_SEARCH_URL = os.environ.get("USERS_SEARCH_URL")


def calculate_amount_of_pagination_pages(elem_amount: int):
    """
    Calculates how many pages are needed to get all
    elements.
    If there is a remainder of division by one hundred,
    for the remaining elements extra page is needed.
    For example:
    to get 100 elements one page is needed,
    but for 101 elements two pages are needed
    (getting extra page, because there is a remainder).
    """
    if elem_amount % PAGE_SIZE != 0:
        return elem_amount // PAGE_SIZE + 1
    return elem_amount // PAGE_SIZE


def construct_search_params(page: int, ids: List[int]):
    """
    With this params assets will return
    list of elements, where ids of elements matches with provided ids.
    """
    return {
        "pagination": {"page_num": page + 1, "page_size": PAGE_SIZE},
        "filters": [
            {
                "field": "id",
                "operator": "in",
                "value": ids[page * PAGE_SIZE : (page + 1) * PAGE_SIZE],
            }
        ],
        "sorting": [{"field": "id", "direction": "asc"}],
    }


def get_response(
    ids: List[int], url: str, tenant: str, token: str
) -> List[dict]:
    """
    Request from jobs or assets microservices all elements,
    that have provided ids.
    Because microservices return only 100 elements, function
    should do several requests.
    Examples of responses are in module docstring.
    """
    complete_response = []
    amount_of_pagination_pages = calculate_amount_of_pagination_pages(len(ids))

    for page in range(amount_of_pagination_pages):
        post_params = construct_search_params(page, ids)
        try:
            response = requests.post(
                url,
                headers={
                    HEADER_TENANT: tenant,
                    AUTHORIZATION: f"{BEARER} {token}",
                },
                json=post_params,
                timeout=5,
            )
        except (ConnectionError, Timeout, RequestException) as err:
            raise_request_exception(err)
        if response.status_code != 200:
            raise_request_exception(response.text)
        complete_response.extend(response.json()["data"])

    return complete_response


def get_response_from_users_search(
    users_ids: List[str], tenant: str, token: str
) -> List[dict]:

    post_params = {
        "filters": [{"field": "id", "operator": "in", "value": users_ids}]
    }

    try:
        response = requests.post(
            USERS_SEARCH_URL,
            headers={
                HEADER_TENANT: tenant,
                AUTHORIZATION: f"{BEARER} {token}",
            },
            json=post_params,
            timeout=5,
        )
    except (ConnectionError, Timeout, RequestException) as err:
        raise_request_exception(err)
    if response.status_code != 200:
        raise_request_exception(response.text)

    return response.json()


def get_user_names_by_request(user_ids: List[str], tenant: str, token: str):
    users_data = get_response_from_users_search(user_ids, tenant, token)
    return {u["id"]: u["username"] for u in users_data}


def expand_response(
    tasks: List[ManualAnnotationTask],
    file_names: Dict[int, str],
    job_names: Dict[int, str],
    user_logins: Dict[str, str],
) -> List[ExpandedManualAnnotationTaskSchema]:
    """
    Add to manual annotation tasks fields file, job, and login
    containing their id and name and delete fields
    job_id and file_id.
    """
    response = []
    for task in tasks:
        response_task = row_to_dict(task)
        response_task["file"] = {
            "id": response_task.pop("file_id"),
            "name": file_names.get(task.file_id, None),
        }
        response_task["job"] = {
            "id": response_task.pop("job_id"),
            "name": job_names.get(task.job_id, None),
        }

        attribute_user_dict = {"id": response_task.get("user_id")}
        if user_logins:
            attribute_user_dict.update(
                {"name": user_logins.get(response_task.get("user_id"))}
            )
        response_task["user"] = attribute_user_dict

        response.append(ExpandedManualAnnotationTaskSchema(**response_task))
    return response


def raise_request_exception(error: str):
    raise HTTPException(
        status_code=500,
        detail=f"Error: {error}",
    )
