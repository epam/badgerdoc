import uuid
from playwright.sync_api import Page, expect
from helpers.files.file_client_frontend import FrontendFileHelper
from logging import getLogger
import datetime

logger = getLogger(__name__)


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


def select_language(page: Page, language: str = None):
    if language:
        logger.info(f"Select language: {language}")
        page.get_by_role("textbox", name="Please select").click()
        page.get_by_text(language, exact=True).click()
        page.get_by_role("button", name="Next").click()


def fill_job_and_start(
    page: Page, jobs_client, job_name: str, pipeline_manager=None, pipeline="print", save_as_draft=False
):
    job_name = job_name if job_name else f"test_job_{uuid.uuid4().hex[:8]}"
    logger.info(f"Fill job name: {job_name}")
    page.get_by_role("textbox", name="Job name").fill(job_name)

    if pipeline_manager:
        logger.info(f"Select pipeline manager: {pipeline_manager}")
        page.get_by_text(pipeline_manager).nth(1).click()

    logger.info("Select pipeline dropdown")
    page.get_by_role("textbox", name="Select pipeline").click()
    page.get_by_text(pipeline, exact=True).click()

    if save_as_draft:
        logger.info("Save as draft")
        page.get_by_role("button", name="Save as Draft").click()
    else:
        logger.info("Start extraction")
        page.get_by_role("button", name="Start Extraction").click()
    page.wait_for_url("**/jobs/**", timeout=20000)
    jobs = jobs_client.search_jobs()
    job_id = next((j["id"] for j in jobs["data"] if j["name"] == job_name), None)
    assert job_id, f"Job with name {job_name} not found!"
    if not save_as_draft:
        jobs_client.poll_until_finished(job_id, timeout_seconds=180)
        page.reload()
        expect(page.get_by_text("Finished")).to_be_visible(timeout=10000)
    else:
        page.reload()
        expect(page.get_by_text("Draft")).to_be_visible(timeout=10000)


def select_human_in_the_loop_and_start(
    page: Page,
    jobs_client,
    job_name: str,
    validation_type: str = "Cross validation",
    day: str | None = None,
    annotator: str = "admin",
    categories: list[str] = None,
    distribute_tasks: bool = False,
):
    if not categories:
        categories = ["Age"]
    logger.info("Select Human in the loop")
    page.get_by_role("tab", name="Human in the Loop").click()

    logger.info("Select validation type")
    page.get_by_role("textbox", name="Select validation type").click()
    page.get_by_text(validation_type, exact=True).click()

    page.get_by_role("textbox", name="DD/MM/YYYY").click()
    if not day:
        day = datetime.datetime.today().day + 1
    logger.info(f"Select date {day}")
    page.get_by_text(str(day), exact=True).click()

    logger.info("Select annotator")
    page.get_by_role("textbox", name="Select Annotators and").click()
    page.get_by_role("listbox").get_by_text(annotator).click(force=True)
    page.locator(".uui-input-box.-clickable.uui-focus").click()

    page.get_by_role("textbox", name="Select categories").click()
    for category in categories:
        logger.info(f"Select category: {category}")
        page.get_by_text(category, exact=True).click()

    if distribute_tasks:
        logger.info("Distribute annotation tasks")
        page.get_by_text("Distribute annotation tasks").click()

    fill_job_and_start(page, jobs_client, job_name)


def prepare_files(page: Page, file_tracker, frontend_file_helper: FrontendFileHelper, tmp_path, num_files, client):
    logger.info(f"Prepare {num_files} temp files")
    temp_files = frontend_file_helper.prepare_temp_files(tmp_path, num_files=num_files)
    files = frontend_file_helper.upload_files(page, temp_files, file_tracker=file_tracker, client=client)
    return files


def select_files(page: Page, document_names):
    logger.info(f"Select files: {document_names}")
    for file_name in document_names:
        row = page.locator(f"text={file_name}").first
        print(f'clicking file "{file_name}"')
        checkbox_label = row.locator("xpath=preceding-sibling::label")
        checkbox_label.click(force=True)


def select_first_element(page: Page):
    logger.info("Select first element in the table")
    first_row = page.locator('div[role="row"]').nth(1)
    checkbox = first_row.locator("label.uui-checkbox-container")
    checkbox.click(force=True)


def run_upload_workflow(
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
    human_in_loop: bool = False,
    pipeline_manager: str = None,
):
    logger.info("Open wizard")
    page.get_by_role("button", name="Upload Wizard").click()

    prepare_files(page, file_tracker, frontend_file_helper, tmp_path, num_files, client)

    select_dataset(page, dataset_type, dataset_name)

    select_preprocessor(page, preprocessor=preprocessor, click_next=not language)

    select_language(page, language)

    if human_in_loop:
        select_human_in_the_loop_and_start(page, jobs_client, job_name)
    else:
        fill_job_and_start(page, jobs_client, job_name=job_name, pipeline_manager=pipeline_manager)


def create_file_in_dataset(
    dataset_tracker,
    file_tracker,
    tmp_path,
    num_files,
):
    created_datasets, dataset_client = dataset_tracker
    dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
    dataset = dataset_client.create_dataset(name=dataset_name)
    created_datasets.append(dataset_name)
    assert "successfully created" in dataset["detail"].lower()
    first_dataset_id = dataset_client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])[
        "data"
    ][0]["id"]

    created_files, client = file_tracker
    for i in range(num_files):
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        file_id = file_info["id"]
        move1 = client.move_files(name=dataset_name, objects=[file_id])[0]
        assert move1["status"] is True
        assert "successfully bounded" in move1["message"].lower()
        files_in_first = dataset_client.search_files(dataset_id=first_dataset_id)["data"]
        assert any(f["id"] == file_id for f in files_in_first)
    files = [file["file_name"] for file in created_files]
    return dataset_name, files


def run_new_job_documents_workflow(
    page: Page,
    num_files: int,
    file_tracker,
    jobs_client,
    dataset_tracker,
    tmp_path=None,
    job_name: str = None,
    human_in_loop: bool = False,
    validation_type="Cross validation",
    pipeline_manager: str = None,
    distribute_tasks: bool = False,
):
    dataset_name, files = create_file_in_dataset(
        dataset_tracker=dataset_tracker, tmp_path=tmp_path, num_files=num_files, file_tracker=file_tracker
    )

    logger.info("Open wizard")
    page.get_by_role("button", name="New job").click()

    select_files(page, files)
    page.get_by_role("button", name="Next").click()

    if human_in_loop:
        select_human_in_the_loop_and_start(
            page, jobs_client, job_name, validation_type=validation_type, distribute_tasks=distribute_tasks
        )
    else:
        if pipeline_manager == "Other":
            fill_job_and_start(
                page, jobs_client, job_name=job_name, pipeline_manager=pipeline_manager, pipeline="AI by MCP"
            )
        else:
            fill_job_and_start(page, jobs_client, job_name=job_name, pipeline_manager=pipeline_manager)


def run_new_job_first_line_workflow(
    page: Page,
    num_files: int,
    file_tracker,
    jobs_client,
    dataset_tracker,
    tab_button,
    tmp_path=None,
    job_name: str = None,
    human_in_loop: bool = False,
    pipeline_manager: str = None,
    save_as_draft: bool = False,
):
    dataset_name, files = create_file_in_dataset(
        dataset_tracker=dataset_tracker, tmp_path=tmp_path, num_files=num_files, file_tracker=file_tracker
    )
    logger.info("Open wizard")
    page.get_by_role("button", name="New job").click()
    page.get_by_role("tab", name=tab_button, exact=True).click()
    if tab_button == "Datasets":
        select_files(page, [dataset_name])
    else:
        select_first_element(page)
    page.get_by_role("button", name="Next").click()

    if human_in_loop:
        select_human_in_the_loop_and_start(page, jobs_client, job_name)
    else:
        fill_job_and_start(
            page, jobs_client, job_name=job_name, pipeline_manager=pipeline_manager, save_as_draft=save_as_draft
        )


def run_new_job_multi_tab_workflow(
    page: Page,
    jobs_client,
    file_tracker,
    dataset_tracker,
    tmp_path,
    tabs: list[str],
    num_files=1,
    job_name: str = None,
    human_in_loop: bool = False,
    pipeline_manager: str = None,
):
    logger.info(f"Preparing temp document for tabs: {tabs}")
    dataset_name, files = create_file_in_dataset(
        dataset_tracker=dataset_tracker, tmp_path=tmp_path, num_files=num_files, file_tracker=file_tracker
    )

    logger.info("Open wizard")
    page.get_by_role("button", name="New job").click()

    for tab in tabs:
        logger.info(f"Go to tab: {tab}")
        page.get_by_role("tab", name=tab, exact=True).click()

        if tab == "Documents":
            select_files(page, files)
        else:
            select_first_element(page)

    page.get_by_role("button", name="Next").click()

    if human_in_loop:
        select_human_in_the_loop_and_start(page, jobs_client, job_name)
    else:
        fill_job_and_start(page, jobs_client, job_name=job_name, pipeline_manager=pipeline_manager)


def run_new_job_dataset_without_documents_workflow(
    page: Page,
    jobs_client,
    dataset_tracker,
    job_name: str = None,
    human_in_loop: bool = False,
    pipeline_manager: str = None,
):
    created_datasets, dataset_client = dataset_tracker
    dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
    dataset = dataset_client.create_dataset(name=dataset_name)
    created_datasets.append(dataset_name)
    assert "successfully created" in dataset["detail"].lower()

    logger.info("Open wizard")
    page.get_by_role("button", name="New job").click()
    page.get_by_role("tab", name="Datasets", exact=True).click()

    select_files(page, [dataset_name])
    page.get_by_role("button", name="Next").click()

    if human_in_loop:
        select_human_in_the_loop_and_start(page, jobs_client, job_name)
    else:
        fill_job_and_start(page, jobs_client, job_name=job_name, pipeline_manager=pipeline_manager)
