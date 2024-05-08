from unittest.mock import patch

import pytest
import requests
from pipelines import http_utils, schemas


def test_make_request(request_mock):
    """Testing make_request."""
    body = {"job_id": 1, "status": schemas.JobStatus.DONE}
    http_utils.make_request(url="asd", body=body)
    request_mock.assert_called_once_with(
        method="PUT", url="asd", json=body, data=None, headers=None
    )


@pytest.mark.parametrize(
    ["s_effect", "expected", "call_count"],
    [
        (["foo", requests.ConnectionError()], "foo", 1),
        ([requests.ConnectionError(), "foo"], "foo", 2),
        ([requests.ConnectionError()] * 3, None, 3),
    ],
)
def test_make_request_with_retry(s_effect, expected, call_count, request_mock):
    """Testing make_request_with_retry."""
    with patch(
        "pipelines.http_utils.make_request", side_effect=s_effect
    ) as req_mock:
        assert http_utils.make_request_with_retry("", {}, start=0) == expected
        assert req_mock.call_count == call_count


@pytest.mark.parametrize("retries", [-1, 0])
def test_make_request_with_retry_wrong_retries_value(retries):
    """Testing make_request_with_retry when retries number is wrong."""
    with pytest.raises(ValueError):
        http_utils.make_request_with_retry("", {}, retries=retries)
