import uuid
import pytest
from playwright.sync_api import Page, expect
from helpers.files.file_client_frontend import FrontendFileHelper
from logging import getLogger
from pathlib import Path
from helpers.steps.jobs_creation import run_upload_workflow

logger = getLogger(__name__)


class TestUploadWizard:
    @pytest.mark.parametrize("num_files", [1, 3])
    @pytest.mark.parametrize("manager", [None, "Airflow", "Databricks"])
    def test_upload_documents_without_dataset(
        self, logged_in_page: Page, file_tracker, tmp_path, jobs_client, file_client, num_files, manager
    ):
        page = logged_in_page
        created_files, client = file_tracker
        frontend_file_helper = FrontendFileHelper()
        run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            pipeline_manager=manager,
            dataset_type="none",
            tmp_path=tmp_path,
        )

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_existing_dataset(
        self, logged_in_page: Page, file_tracker, tmp_path, jobs_client, file_client, dataset_tracker, num_files
    ):
        page = logged_in_page
        created_files, client = file_tracker
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        first_resp = dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)
        assert "successfully created" in first_resp["detail"].lower()

        frontend_file_helper = FrontendFileHelper()
        run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="existing",
            dataset_name=dataset_name,
            tmp_path=tmp_path,
        )

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_existing_dataset_new_name(
        self, logged_in_page: Page, file_tracker, tmp_path, jobs_client, file_client, dataset_tracker, num_files
    ):
        # should we see an error here?
        page = logged_in_page
        created_files, client = file_tracker
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        first_resp = dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)
        assert "successfully created" in first_resp["detail"].lower()

        frontend_file_helper = FrontendFileHelper()
        run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="news",
            dataset_name=dataset_name,
            tmp_path=tmp_path,
        )

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_new_dataset(
        self, logged_in_page: Page, file_tracker, tmp_path, jobs_client, file_client, dataset_tracker, num_files
    ):
        page = logged_in_page
        created_files, client = file_tracker
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        created_datasets.append(dataset_name)

        frontend_file_helper = FrontendFileHelper()
        run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="new",
            dataset_name=dataset_name,
            tmp_path=tmp_path,
        )

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_with_language(
        self,
        logged_in_page: Page,
        file_tracker,
        tmp_path,
        jobs_client,
        file_client,
        num_files,
    ):
        page = logged_in_page
        created_files, client = file_tracker
        frontend_file_helper = FrontendFileHelper()

        run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="none",
            tmp_path=tmp_path,
            language="English",
        )

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_any_preprocessor(
        self,
        logged_in_page: Page,
        file_tracker,
        tmp_path,
        jobs_client,
        file_client,
        num_files,
    ):
        page = logged_in_page
        created_files, client = file_tracker
        frontend_file_helper = FrontendFileHelper()

        run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="none",
            tmp_path=tmp_path,
            preprocessor="any",
        )

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_all_settings_new_job_name(
        self,
        logged_in_page: Page,
        file_tracker,
        tmp_path,
        jobs_client,
        file_client,
        num_files,
    ):
        page = logged_in_page
        created_files, client = file_tracker
        frontend_file_helper = FrontendFileHelper()

        run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="none",
            tmp_path=tmp_path,
            preprocessor="any",
            language="English",
        )

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_all_settings_existing_job_name(
        self,
        logged_in_page: Page,
        file_tracker,
        tmp_path,
        jobs_client,
        file_client,
        num_files,
        dataset_client,
        dataset_tracker,
        user_uuid,
        job_tracker,
    ):
        # should we get an error here as well?
        # create a job
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

        # run wizard
        page = logged_in_page
        created_files, client = file_tracker
        frontend_file_helper = FrontendFileHelper()

        run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="none",
            tmp_path=tmp_path,
            preprocessor="any",
            language="English",
            job_name=job_name,
        )

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_invalid_format(self, tmp_path, logged_in_page, num_files):
        page = logged_in_page
        temp_files = []
        for i in range(num_files):
            invalid_file = Path(tmp_path / f"{uuid.uuid4().hex}.py")
            invalid_file.write_text("this is py file")
            temp_files.append(invalid_file)

        logger.info("Open wizard")
        page.get_by_role("button", name="Upload Wizard").click()
        page.locator("input[type='file']").set_input_files([str(f) for f in temp_files])
        page.get_by_role("button", name="Next").click()
        try:
            expect(page.locator("text=Error occurred")).to_be_visible(timeout=2000)
            logger.info("Error message appeared as expected")
        except TimeoutError:
            pytest.fail("Expected error message did not appear")

    @pytest.mark.skip(reason="Returns 500 even in browser")
    @pytest.mark.parametrize("num_files", [1, 3])
    def test_human_in_the_loop(self, logged_in_page: Page, num_files, file_tracker, jobs_client, tmp_path):
        page = logged_in_page
        created_files, client = file_tracker
        frontend_file_helper = FrontendFileHelper()
        run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="none",
            tmp_path=tmp_path,
            human_in_loop=True,
        )
