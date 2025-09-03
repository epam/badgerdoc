from logging import getLogger
from datetime import datetime, timedelta
import uuid

import pytest


logger = getLogger(__name__)


class TestJobs:
    def test_create_and_poll_job(
        self, file_client, jobs_client, file_tracker, dataset_tracker, job_tracker, tmp_path, user_uuid
    ):
        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_ds_{uuid.uuid4().hex[:8]}"
        dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)
        move_resp = file_client.move_files(name=dataset_name, objects=[file_info["id"]])[0]
        assert move_resp["status"] is True
        job_name = f"test_job_{uuid.uuid4().hex[:8]}"
        create_resp = jobs_client.create_job(
            name=job_name,
            file_ids=[file_info["id"]],
            owners=[user_uuid],
        )
        job_tracker[0].append(create_resp)
        job_id = create_resp.get("id")
        assert job_id
        final_job = jobs_client.poll_until_finished(job_id=job_id, timeout_seconds=300)
        status = final_job.get("status")
        assert str(status).lower() in {"finished", "success", "completed"}
        job_files = final_job.get("files") or []
        assert file_info["id"] in job_files

    @pytest.mark.parametrize("field", ["name", "type", "status", "deadline", "creation_datetime"])
    @pytest.mark.parametrize("direction", ["asc", "desc"])
    # descending name sorting works weird
    def test_sorting(self, jobs_client, field, direction):
        resp = jobs_client.post_json(
            "/jobs/jobs/search",
            json={
                "pagination": {"page_num": 1, "page_size": 15},
                "filters": [],
                "sorting": [{"direction": direction, "field": field}],
            },
            headers=jobs_client._default_headers(content_type_json=True),
        )
        data = resp["data"]
        values = [d[field] for d in data if field in d and d[field] is not None]

        if field in {"creation_datetime", "deadline"}:
            values = [datetime.fromisoformat(v) for v in values]

        expected = sorted(values, reverse=(direction == "desc"))
        assert values == expected

    @pytest.mark.parametrize("field", ["name", "type", "status", "deadline", "creation_datetime"])
    def test_job_search(self, jobs_client, job_tracker, file_tracker, dataset_tracker, user_uuid, tmp_path, field):
        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_ds_{uuid.uuid4().hex[:8]}"
        dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)

        job_name = f"test_job_{uuid.uuid4().hex[:8]}"
        create_resp = jobs_client.create_job(
            name=job_name,
            file_ids=[file_info["id"]],
            owners=[user_uuid],
        )
        job_id = create_resp.get("id")
        jobs_client.poll_until_finished(job_id=job_id, timeout_seconds=300)
        job_tracker[0].append(create_resp)
        search_value = create_resp.get(field, None)

        filters = [
            {"field": field, "operator": "eq", "value": search_value},
            {"field": "name", "operator": "eq", "value": job_name},
        ]

        search_resp = jobs_client.post_json(
            "/jobs/jobs/search",
            json={
                "pagination": {"page_num": 1, "page_size": 100},
                "filters": filters,
            },
            headers=jobs_client._default_headers(content_type_json=True),
        )

        job_ids = [j["id"] for j in search_resp["data"]]
        assert job_id in job_ids

    @pytest.mark.parametrize("field", ["creation_datetime", "deadline"])
    def test_date_range_filter(self, jobs_client, field):
        start = (datetime.utcnow() - timedelta(days=365)).replace(microsecond=0).isoformat()
        end = (datetime.utcnow() + timedelta(days=365)).replace(microsecond=0).isoformat()

        resp = jobs_client.post_json(
            "/jobs/jobs/search",
            json={
                "pagination": {"page_num": 1, "page_size": 15},
                "filters": [
                    {"field": field, "operator": "ge", "value": start},
                    {"field": field, "operator": "le", "value": end},
                ],
            },
            headers=jobs_client._default_headers(content_type_json=True),
        )

        data = resp["data"]
        for job in data:
            if field in job and job[field] is not None:
                date_val = datetime.fromisoformat(job[field])
                assert datetime.fromisoformat(start) <= date_val <= datetime.fromisoformat(end)
