from logging import getLogger

import pytest


from helpers.base_client.base_client import HTTPError

logger = getLogger(__name__)


class TestReports:
    def test_export_tasks_csv(self, reports_client, user_uuid):
        csv_text = reports_client.export_tasks(
            user_ids=[user_uuid],
            date_from="2025-05-01 00:00:00",
            date_to="2025-08-31 00:00:00",
        )
        assert "annotator_id" in csv_text
        assert "task_id" in csv_text

    @pytest.mark.parametrize(
        "date_from,date_to",
        [
            ("2028-05-01 00:00:00", "2028-08-31 00:00:00"),
            ("1900-01-01 00:00:00", "1900-12-31 00:00:00"),
            ("2025-09-01 00:00:00", "2025-08-01 00:00:00"),
        ],
    )
    def test_export_tasks_wrong_date(self, reports_client, user_uuid, date_from, date_to):
        with pytest.raises(HTTPError) as exc:
            reports_client.export_tasks(
                user_ids=[user_uuid],
                date_from=date_from,
                date_to=date_to,
            )
        assert exc.value.status_code == 406
