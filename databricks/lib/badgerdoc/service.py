from typing import Any, Dict

import requests

TIMEOUT = 10


class BadgerDocService:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self._token = self.get_token()

    def get_token(self) -> str:
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": "admin-cli",
        }
        token_url = f"{self.host}/users/token"
        response = requests.post(token_url, data=data, timeout=TIMEOUT)

        if response.status_code != 200:
            raise requests.exceptions.HTTPError(
                f"Failed to get token from {token_url}. "
                f"Status code: {response.status_code}"
            )

        token = response.json()["access_token"]

        return str(token)

    def get_annotations(
        self, tenant: str, job_id: int, file_id: int, revision_id: str
    ) -> Dict[str, str]:

        headers = {
            "X-Current-Tenant": tenant,
            "Authorization": f"Bearer {self._token}",
        }
        annotation_url = (
            f"{self.host}/annotation/annotation/{job_id}/{file_id}/"
            f"{revision_id}"
        )

        response = requests.get(
            annotation_url, headers=headers, timeout=TIMEOUT
        ).json()

        if not response.get("revision"):
            raise ValueError(
                f"Failed to get annotations for revision job_id:{job_id}, "
                f"file_id:{file_id}, revision_id:{revision_id}"
            )

        return dict(response)

    def commit_annotation(
        self, tenant: str, job_id: int, file_id: int, body: Dict[str, Any]
    ) -> None:

        headers = {
            "X-Current-Tenant": tenant,
            "Authorization": f"Bearer {self._token}",
        }
        annotation_url = (
            f"{self.host}/annotation/annotation/{job_id}/{file_id}"
        )

        requests.post(url=annotation_url, headers=headers, json=body)

        # if response.status_code not in [200, 201]:
        #     raise requests.exceptions.RequestException(
        #         f"Failed to commit annotation for job_id:{job_id}, file_id:{file_id}, body: {body}"
        #     )

    def start_job(self, tenant: str, job_id: int) -> None:

        start_job_url = f"{self.host}/annotation/jobs/{job_id}/start"
        headers = {
            "X-Current-Tenant": tenant,
            "Authorization": f"Bearer {self._token}",
        }

        response = requests.post(url=start_job_url, headers=headers)

        if response.status_code not in [200, 201]:
            raise requests.exceptions.RequestException(
                f"Failed to start job {job_id}. Status code: {response.status_code}, Response: {response.text}"
            )

    def finish_job(self, tenant: str, job_id: int) -> None:

        job_url = f"{self.host}/jobs/jobs/{job_id}"
        headers = {
            "X-Current-Tenant": tenant,
            "Authorization": f"Bearer {self._token}",
        }

        response = requests.put(
            url=job_url,
            json={"status": "Finished"},
            timeout=5,
            headers=headers,
        )

        if response.status_code not in [200, 201]:
            raise requests.exceptions.RequestException(
                f"Failed to finish job {job_id}. Status code: {response.status_code}, Response: {response.text}"
            )
