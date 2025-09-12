import uuid
import pytest
from playwright.sync_api import Page, expect
from helpers.files.file_client_frontend import FrontendFileHelper
from logging import getLogger
from pathlib import Path


logger = getLogger(__name__)


class TestUploadWizard:
    @staticmethod
    def select_dataset(page: Page, dataset_type: str, dataset_name: str = None):
        logger.info(f"Select dataset option: {dataset_type}")
        if dataset_type == "none":
            page.locator("label:has-text('No') div").nth(1).click()
        elif dataset_type == "existing":
            page.locator("label:has-text('Existing dataset') div").nth(1).click()
            page.locator(".uui-icon.uui-enabled.uui-icon-dropdown").click()
            page.get_by_text(dataset_name, exact=True).click()
        elif dataset_type == "new":
            page.locator("label:has-text('New dataset') div").nth(1).click()
            page.get_by_role("textbox", name="Dataset name").fill(dataset_name)
        else:
            raise ValueError(f"Unknown dataset_type: {dataset_type}")
        page.get_by_role("button", name="Next").click()

    @staticmethod
    def select_preprocessor(page: Page, preprocessor: str = None, click_next: bool = True) -> None:
        logger.info(f"Select preprocessor: {preprocessor or 'No need'}")
        if preprocessor is None:
            page.get_by_text("No need for preprocessor").click()
        elif preprocessor == "any":
            preprocessor_section = page.get_by_text("Select preprocessor").locator("..").locator("..")
            preprocessor_section.locator("label").nth(1).click()
        else:
            page.get_by_text(preprocessor, exact=True).click()
        if click_next:
            page.get_by_role("button", name="Next").click()

    @staticmethod
    def select_language(page: Page, language: str = None):
        if language:
            logger.info(f"Select language: {language}")
            page.get_by_role("textbox", name="Please select").click()
            page.get_by_text(language, exact=True).click()
            page.get_by_role("button", name="Next").click()

    @staticmethod
    def fill_job_and_start(page: Page, jobs_client, job_name: str):
        job_name = job_name if job_name else f"test_job_{uuid.uuid4().hex[:8]}"
        logger.info(f"Fill job name: {job_name}")
        page.get_by_role("textbox", name="Job name").fill(job_name)

        logger.info("Select pipeline dropdown")
        page.locator(".uui-icon.uui-enabled.uui-icon-dropdown").click()
        page.get_by_text("print", exact=True).click()

        logger.info("Start extraction")

        page.get_by_role("button", name="Start Extraction").click()
        page.wait_for_url("**/jobs/**", timeout=20000)
        jobs = jobs_client.search_jobs()
        job_id = next((j["id"] for j in jobs["data"] if j["name"] == job_name), None)
        assert job_id, f"Job with name {job_name} not found!"
        jobs_client.poll_until_finished(job_id, timeout_seconds=180)
        page.reload()
        expect(page.get_by_text("Finished")).to_be_visible(timeout=10000)

    def run_upload_workflow(
        self,
        page: Page,
        frontend_file_helper: FrontendFileHelper,
        num_files: int,
        file_tracker,
        client,
        jobs_client,
        dataset_type: str = "none",  # "none", "existing", "new"
        dataset_name: str = None,
        tmp_path=None,
        language: str = None,
        preprocessor: str = None,
        job_name: str = None,
    ):
        logger.info("Open wizard")
        page.get_by_role("button", name="Upload Wizard").click()

        logger.info(f"Prepare {num_files} temp files")
        temp_files = frontend_file_helper.prepare_temp_files(tmp_path, num_files=num_files)
        frontend_file_helper.upload_files(page, temp_files, file_tracker=file_tracker, client=client)

        self.select_dataset(page, dataset_type, dataset_name)

        self.select_preprocessor(page, preprocessor=preprocessor, click_next=not language)

        self.select_language(page, language)

        return self.fill_job_and_start(page, jobs_client, job_name=job_name)

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_without_dataset(
        self, logged_in_page: Page, file_tracker, tmp_path, jobs_client, file_client, num_files
    ):
        page = logged_in_page
        created_files, client = file_tracker
        frontend_file_helper = FrontendFileHelper()
        self.run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
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
        self.run_upload_workflow(
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
        self.run_upload_workflow(
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
        self.run_upload_workflow(
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

        self.run_upload_workflow(
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

        self.run_upload_workflow(
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

        self.run_upload_workflow(
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

        self.run_upload_workflow(
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
