from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

import badgerdoc_storage
import magic
import minio
import pdf2image
import PIL.Image
import requests
import sqlalchemy.orm
import starlette.datastructures

from assets import db, exceptions, logger, schemas
from assets.config import settings
from assets.utils import chem_utils, minio_utils
from assets.utils.convert_service_utils import post_pdf_to_convert

logger_ = logger.get_logger(__name__)


def converter_by_extension(ext: str) -> Callable[[bytes], Any]:
    pass


def to_obj(
    id_: Optional[int],
    action: str,
    action_status: bool,
    message: str,
    name: Optional[str] = None,
) -> schemas.ActionResponse:
    object_ = to_dict(action, action_status, id_, message, name)
    return schemas.ActionResponse.parse_obj(object_)


class ActionResponseTypedDict(TypedDict):
    file_name: Optional[str]
    id: Optional[int]
    action: str
    status: bool
    message: str


def to_dict(
    action: str,
    action_status: bool,
    id_: Optional[int],
    message: str,
    name: Optional[str] = None,
) -> ActionResponseTypedDict:
    return ActionResponseTypedDict(
        file_name=name,
        id=id_,
        action=action,
        status=action_status,
        message=message,
    )


def get_mimetype(file: bytes) -> Any:
    mimetype = magic.from_buffer(file, mime=True)
    return mimetype


def get_pages(file: bytes, ext: str) -> Any:
    logger_.info("Getting count of pages by file extension: %s", ext)
    if ext not in chem_utils.SUPPORTED_FORMATS:
        raise exceptions.AssetsUnsupportedFileFormat(
            "File extension %s is not supported", ext
        )
    if "chem" == chem_utils.SUPPORTED_FORMATS[ext]:
        return chem_utils.get_page_count(file, ext)
    if "text" == chem_utils.SUPPORTED_FORMATS[ext]:
        return 1
    # Pdf as default
    return get_pages_from_pdf(file) or get_pages_from_image(file)


def get_pages_from_pdf(file: bytes) -> Any:
    try:
        pages = pdf2image.pdfinfo_from_bytes(file)["Pages"]
    except Exception:
        return None
    return pages


def get_pages_from_image(file: bytes) -> Any:
    try:
        with PIL.Image.open(BytesIO(file)) as image:
            pages = image.n_frames
    except Exception:
        return None
    return pages


def get_file_size(file_bytes: bytes) -> int:
    return len(file_bytes)


def check_uploading_limit(
    files_list: List[Union[str, starlette.datastructures.UploadFile]],
) -> Any:
    limit = settings.uploading_limit
    if len(files_list) > limit:
        raise exceptions.UploadLimitExceedError(
            f"Current limit for uploading is {settings.uploading_limit}!"
        )


def process_s3_files(
    bucket_storage: str,
    s3_files: Dict[str, BytesIO],
    session: sqlalchemy.orm.Session,
    storage: minio.Minio,
) -> List[ActionResponseTypedDict]:
    """
    Applies file processing to each S3 files
    """
    result = []
    for file_key, file_ in s3_files.items():
        file_processor = FileProcessor(
            file=file_,
            storage=storage,
            session=session,
            bucket_storage=bucket_storage,
            file_key=file_key,
        )
        file_processor.run()
        result.append(file_processor.response)

    return result


def process_form_files(
    tenant: str,
    form_files: List[Any],
    session: sqlalchemy.orm.Session,
) -> List[ActionResponseTypedDict]:
    """
    Applies file processing to each form uploaded files
    """
    result = []
    bd_storage = badgerdoc_storage.storage.get_storage(tenant)
    for file_ in form_files:
        file_processor = FileProcessor(
            file=file_, storage=bd_storage, session=session
        )
        file_processor.run()
        result.append(file_processor.response)

    return result


def is_gotenberg_returns_file(gotenberg_output: bytes) -> bool:
    """
    Checks if file was converted to pdf.
    """
    return bool(get_mimetype(gotenberg_output) == "application/pdf")


class FileConverter:
    """
    Converts:
    documents and vector images to pdf format through Gotenberg and convert
    service raster images to jpeg format
    """

    def __init__(
        self,
        file_bytes: bytes,
        file_name: str,
        ext: str,
        bucket_storage: str,
        blank_db_file,
        storage: badgerdoc_storage.storage.BadgerDocStorage,
    ) -> None:
        self.bucket_storage = bucket_storage
        self.file_bytes = file_bytes
        self.file_name = file_name
        self.new_file = blank_db_file
        self.ext: str = ext
        self.conversion_status: Optional[schemas.ConvertionStatus] = None
        self.converted_file: Optional[bytes] = None
        self.converted_ext: Optional[str] = None
        self.storage = storage

    @property
    def _output_pdf_path(self) -> str:
        return f"files/{self.new_file.id}/{self.new_file.id}.pdf"

    @property
    def _output_tokens_path(self) -> str:
        return f"files/{self.new_file.id}/ocr/1.json"

    @property
    def _tmp_file_name(self) -> str:
        return f"{self.new_file.id}.pdf"

    def convert_to_pdf(self) -> bytes:
        """
        Converts file to pdf format
        """
        buf = BytesIO(self.file_bytes)
        buf.name = self.file_name
        file_ = {"files": (self.file_name, buf)}
        try:
            converted_file = requests.post(
                settings.gotenberg_libre_office_endpoint, files=file_
            )
        except requests.exceptions.ConnectionError as e:
            self.conversion_status = schemas.ConvertionStatus.ERROR
            logger_.error("Gotenberg connection error - detail: %s", e)
            raise requests.exceptions.ConnectionError(e)

        if is_gotenberg_returns_file(converted_file.content) is False:
            #  is_gotenberg_returns_file func checks if file was converted to pdf.  # noqa
            #  In case of some error, the content of Gotenberg response is plain text.  # noqa
            self.conversion_status = schemas.ConvertionStatus.ERROR
            logger_.error("%s with %s", self.conversion_status, self.file_name)
            raise exceptions.FileConversionError
        self.converted_ext = ".pdf"
        self.conversion_status = schemas.ConvertionStatus.CONVERTED_TO_PDF
        return converted_file.content

    def convert_html_to_pdf(self) -> bytes:
        """
        Converts html file to pdf format
        """
        buf = BytesIO(self.file_bytes)
        buf.name = self.file_name
        file_ = {"files": ("index.html", buf)}
        try:
            converted_file = requests.post(
                settings.gotenberg_chromium_endpoint, files=file_
            )
        except requests.exceptions.ConnectionError as e:
            self.conversion_status = schemas.ConvertionStatus.ERROR
            raise requests.exceptions.ConnectionError(e)

        if not is_gotenberg_returns_file(converted_file.content):
            #  is_gotenberg_returns_file func checks if file was converted to pdf.  # noqa
            #  In case of some error, the content of Gotenberg response is plain text.  # noqa
            self.conversion_status = schemas.ConvertionStatus.ERROR
            logger_.error("%s with %s", self.conversion_status, self.file_name)
            raise exceptions.FileConversionError
        self.converted_ext = ".pdf"
        self.conversion_status = schemas.ConvertionStatus.CONVERTED_TO_PDF
        return converted_file.content

    def convert_to_jpg(self) -> bytes:
        """
        Converts file to jpeg format
        """
        buf = BytesIO()
        try:
            img = PIL.Image.open(BytesIO(self.file_bytes))
        except PIL.UnidentifiedImageError:
            self.conversion_status = schemas.ConvertionStatus.ERROR
            logger_.error("%s with %s", self.conversion_status, self.file_name)
            raise exceptions.FileConversionError
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, "JPEG")
        img.close()
        byte_im = buf.getvalue()
        self.converted_ext = ".jpg"
        self.conversion_status = schemas.ConvertionStatus.CONVERTED_TO_JPG
        return byte_im

    def convert_gotenberg_formats(self) -> bytes:
        pdf_from_txt = self.convert_to_pdf()
        file_ = BytesIO(pdf_from_txt)
        self.minio_client.put_object(
            bucket_name=self.bucket_storage,
            object_name=self._output_pdf_path,
            data=file_,
            length=len(pdf_from_txt),
        )
        post_pdf_to_convert(
            self.bucket_storage,
            self._output_pdf_path,
            self._output_tokens_path,
        )
        self.converted_ext = ".pdf"
        self.conversion_status = schemas.ConvertionStatus.CONVERTED_TO_PDF
        converted_file = self.minio_client.fget_object(  # noqa
            self.bucket_storage,
            self._output_pdf_path,
            self._tmp_file_name,
        )
        with open(self._tmp_file_name, "rb") as tmp_file:
            return tmp_file.read()

    def convert_html(self) -> bytes:
        pdf_from_html = self.convert_html_to_pdf()
        file_ = BytesIO(pdf_from_html)
        self.minio_client.put_object(
            bucket_name=self.bucket_storage,
            object_name=self._output_pdf_path,
            data=file_,
            length=len(pdf_from_html),
        )
        post_pdf_to_convert(
            self.bucket_storage,
            self._output_pdf_path,
            self._output_tokens_path,
        )
        self.converted_ext = ".pdf"
        self.conversion_status = schemas.ConvertionStatus.CONVERTED_TO_PDF
        converted_file = self.minio_client.fget_object(  # noqa
            self.bucket_storage,
            self._output_pdf_path,
            self._tmp_file_name,
        )
        with open(self._tmp_file_name, "rb") as tmp_file:
            return tmp_file.read()

    def convert_pdf(self) -> bytes:
        try:
            self.storage.upload_obj(
                target_path=self._output_pdf_path,
                file=BytesIO(self.file_bytes),
            )
        except badgerdoc_storage.storage.BadgerDocStorageResourceExistsError:
            logger_.warning("File %s exists", self._output_pdf_path)
        logger_.debug("File has been uploaded", self.file_name)
        post_pdf_to_convert(
            self.bucket_storage,
            self._output_pdf_path,
            self._output_tokens_path,
        )
        self.converted_ext = ".pdf"
        self.conversion_status = schemas.ConvertionStatus.CONVERTED_TO_PDF
        logger_.debug(f"Got converted {self.file_name}")
        # TODO: It's should be removed,
        # because no real temporary dir is used here
        self.storage.download(self._output_pdf_path, self._tmp_file_name)
        with open(self._tmp_file_name, "rb") as tmp_file:
            return tmp_file.read()

    def convert(self) -> Union[bool]:
        """
        Checks if file format is in the available conversion formats.
        """
        try:
            if self.ext == ".html":
                self.converted_file = self.convert_html()
            if self.ext == ".pdf":
                self.converted_file = self.convert_pdf()
            if self.ext in settings.gotenberg_formats:
                self.converted_file = self.convert_gotenberg_formats()
            if self.ext in settings.image_formats:
                self.converted_file = self.convert_to_jpg()
        except exceptions.FileConversionError:
            return False
        except requests.exceptions.ConnectionError:
            return False

        return True


class FileProcessor:
    """
    Takes S3 or form data files and launch processing pipeline.
    Also checks if any of processing stages have been successful
    """

    def __init__(
        self,
        file: Union[BytesIO, starlette.datastructures.UploadFile],
        storage: badgerdoc_storage.storage.BadgerDocStorage,
        session: sqlalchemy.orm.Session,
        file_key: str = None,
    ) -> None:
        self.response: Optional[ActionResponseTypedDict] = None
        self.action: str = "upload"
        self.session = session
        self.new_file: Optional[db.models.FileObject] = None
        self.storage = storage
        self.ext: Optional[str] = None
        if isinstance(file, BytesIO):
            self.file_bytes = file.read()
            self.file_name = Path(file_key).name
        else:
            self.file_bytes = file.file.read()
            self.file_name = Path(file.filename).name
        self.converted_file: Optional[bytes] = None
        self.converted_file_ext: Optional[str] = None
        self.conversion_status: Optional[str] = None

    def is_extension_correct(self) -> bool:
        """
        Checks if file has an extension
        """
        logger_.debug(f"Checking is_extension_correct {self.file_name}")

        self.ext = Path(self.file_name).suffix
        if self.ext:
            return True
        self.response = to_dict(
            id_=None,
            action=self.action,
            action_status=False,
            message="File has no extension!",
            name=self.file_name,
        )

        return False

    def is_blank_created(self) -> bool:
        """
        Checks if blank row in database was created
        """
        logger_.debug(f"Checking is_blank_created {self.file_name}")

        file_to_upload = self.file_bytes
        file_name = self.file_name
        ext = self.ext
        original_ext = ""
        self.new_file = db.service.insert_file(
            self.session,
            file_name,
            self.storage.tenant,
            get_file_size(file_to_upload),
            ext,
            original_ext,
            get_mimetype(file_to_upload),
            get_pages(file_to_upload, ext),
            schemas.FileProcessingStatus.UPLOADING,
        )
        if ext in (".txt", ".html"):
            self.storage.upload_obj(
                target_path=self.new_file.path,
                file=BytesIO(self.file_bytes),
            )
        else:
            minio_utils.upload_in_minio(  # noqa
                storage=self.storage,
                file=file_to_upload,
                file_obj=self.new_file,
            )

        if self.new_file:
            return True
        self.response = to_dict(
            id_=None,
            action=self.action,
            action_status=False,
            message="Database error",
            name=self.file_name,
        )
        return False

    def is_converted_file(self) -> bool:
        """
        Checks if file was converted
        """
        logger_.debug(f"Checking is_converted_file {self.file_name}")

        converter = FileConverter(
            self.file_bytes,
            self.file_name,
            self.ext,
            self.storage.tenant,
            self.new_file,
            self.storage,
        )
        converter.convert()
        self.conversion_status = converter.conversion_status
        if self.conversion_status is None:
            return True
        if self.conversion_status != "conversion error":
            self.converted_file = converter.converted_file

            self.converted_file_ext = converter.converted_ext
            return True
        self.response = to_dict(
            id_=None,
            action=self.action,
            action_status=False,
            message="Conversion error",
            name=self.file_name,
        )
        return False

    def is_inserted_to_database(self) -> bool:
        """
        Checks if file metadata has been inserted into database
        """
        logger_.debug(f"Checking is_inserted_to_database {self.file_name}")

        if self.converted_file is None:
            file_to_upload = self.file_bytes
            file_name = self.file_name
            ext = self.ext
            original_ext = None
        else:
            file_to_upload = self.converted_file
            file_name = self.file_name
            ext = self.converted_file_ext
            original_ext = self.ext
        self.updated = db.service.update_file(
            self.new_file.id,
            self.session,
            file_name,
            self.storage.tenant,
            get_file_size(file_to_upload),
            ext,
            original_ext,
            get_mimetype(file_to_upload),
            get_pages(file_to_upload, ext),
            schemas.FileProcessingStatus.UPLOADING,
        )
        if self.new_file:
            return True
        self.response = to_dict(
            id_=None,
            action=self.action,
            action_status=False,
            message="Database error",
            name=self.file_name,
        )
        return False

    def is_uploaded_to_storage(self) -> bool:
        """
        Checks if file fas been uploaded to Minio
        """
        logger_.debug(f"Checking is_uploaded_to_storage {self.file_name}")

        if self.converted_file is None:
            file_to_upload = self.file_bytes
        else:
            file_to_upload = self.converted_file

        storage = minio_utils.upload_in_minio(
            self.storage,
            file_to_upload,
            self.new_file,
        )
        if storage:
            return True

        db.service.update_file_status(
            self.new_file.id, schemas.FileProcessingStatus.FAILED, self.session
        )
        self.response = to_dict(
            id_=self.new_file.id,
            action=self.action,
            action_status=False,
            message="S3 Error was raised, try again",
            name=self.file_name,
        )
        return False

    def is_original_file_uploaded_to_storage(self) -> bool:
        logger_.debug(
            f"Checking is_original_file_uploaded_to_storage {self.file_name}"
        )

        if self.conversion_status is None:
            return True
        storage = minio_utils.put_file_to_minio(
            file=self.file_bytes,
            file_obj=self.new_file,
            content_type=get_mimetype(self.file_bytes),
            folder="origin",
            tenant=self.storage.tenant,
        )
        if storage:
            return True
        self.response = to_dict(
            id_=self.new_file.id,
            action=self.action,
            action_status=True,
            message="Origin file version wasn'n uploaded",
            name=self.file_name,
        )
        return False

    def is_file_updated(self) -> bool:
        """
        Checks if file status has been updated
        """
        logger_.debug(f"Checking is_file_updated {self.file_name}")

        upd = db.service.update_file_status(
            self.new_file.id,
            schemas.FileProcessingStatus.UPLOADED,
            self.session,
        )
        if upd:
            self.response = to_dict(
                id_=self.new_file.id,
                action=self.action,
                action_status=True,
                message=f"Successfully uploaded, converted: {self.conversion_status}",  # noqa
                name=self.file_name,
            )
            return True
        return False

    def run(self) -> bool:
        """
        Launch file processing pipeline
        """

        logger_.debug(f"Launch file processing pipeline for {self.file_name=}")

        return (
            self.is_extension_correct()
            and self.is_blank_created()
            and self.is_converted_file()
            and self.is_inserted_to_database()
            and self.is_uploaded_to_storage()
            and self.is_original_file_uploaded_to_storage()
            and self.is_file_updated()
        )
