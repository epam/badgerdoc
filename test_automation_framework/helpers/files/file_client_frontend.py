import uuid
import shutil
from pathlib import Path
from playwright.sync_api import Page
from logging import getLogger
import time

logger = getLogger(__name__)


class FrontendFileHelper:
    @staticmethod
    def prepare_temp_files(tmp_path, num_files=1, suffix="pdf", base_file="multivitamin.pdf"):
        data_dir = Path(__file__).parent.parent.parent / "data"
        original_file = data_dir / base_file
        temp_files = []

        for _ in range(num_files):
            unique_name = f"{uuid.uuid4().hex}.{suffix}"
            temp_file = tmp_path / unique_name
            shutil.copy(original_file, temp_file)
            temp_files.append(temp_file)

        return temp_files

    @staticmethod
    def upload_files(
        page: Page, temp_files, file_tracker=None, client=None, base_file="multivitamin.pdf", timeout_seconds=30
    ):
        page.locator("input[type='file']").set_input_files([str(f) for f in temp_files])

        page.get_by_role("button", name="Next").click()
        success_msgs = page.locator("text=Successfully uploaded, converted")
        end_time = time.time() + timeout_seconds
        while success_msgs.count() < len(temp_files):
            if time.time() > end_time:
                raise RuntimeError(f"Not all upload success messages appeared within {timeout_seconds}s")
            time.sleep(0.5)

        uploaded_infos = []

        if file_tracker is not None and client is not None:
            for temp_file in temp_files:
                end_time = time.time() + timeout_seconds
                while time.time() < end_time:
                    search_resp = client.search_files(
                        filters=[{"field": "original_name", "operator": "eq", "value": temp_file.name}]
                    )
                    if search_resp["data"]:
                        file_info = search_resp["data"][0]
                        file_tracker.append(file_info)
                        uploaded_infos.append(file_info)
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError(f"Uploaded file {temp_file.name} not found in backend after {timeout_seconds}s")

        return uploaded_infos
