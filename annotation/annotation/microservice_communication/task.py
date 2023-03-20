import os
from typing import List

import requests
from dotenv import find_dotenv, load_dotenv
from requests import RequestException

from annotation.errors import AgreementScoreServiceException
from annotation.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from annotation.schemas import (
    AgreementScoreServiceInput,
    AgreementScoreServiceResponse,
)

load_dotenv(find_dotenv())
AGREEMENT_SCORE_SERVICE_URL = os.environ.get("AGREEMENT_SCORE_SERVICE_URL")


def get_agreement_score(
    agreement_scores_input: List[AgreementScoreServiceInput],
    tenant: str,
    token: str,
) -> List[AgreementScoreServiceResponse]:
    body = [score.dict() for score in agreement_scores_input]
    try:
        response = requests.post(
            AGREEMENT_SCORE_SERVICE_URL,
            headers={
                HEADER_TENANT: tenant,
                AUTHORIZATION: f"{BEARER} {token}",
            },
            json=body,
            timeout=5,
        )
        if response.status_code != 200:
            raise AgreementScoreServiceException(response.text)
    except RequestException as exc:
        raise AgreementScoreServiceException(str(exc)) from exc
    return [
        AgreementScoreServiceResponse.construct(**response_score)
        for response_score in response.json()
    ]
