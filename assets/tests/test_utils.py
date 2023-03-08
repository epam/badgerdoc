from io import BytesIO
from tempfile import NamedTemporaryFile
from types import SimpleNamespace
from unittest.mock import Mock, PropertyMock, create_autospec, patch

import pytest
from assets import schemas
from assets.config import settings
from assets.db.models import FileObject
from assets.exceptions import (
    BucketError,
    FileConversionError,
    FileKeyError,
    UploadLimitExceedError,
)
from assets.schemas import ActionResponse
from assets.utils import minio_utils
from assets.utils.common_utils import (
    FileConverter,
    FileProcessor,
    check_uploading_limit,
    to_obj,
)
from assets.utils.s3_utils import S3Manager
from minio import Minio
from PIL import Image
from requests import Response
from sqlalchemy.orm import Session

ID_ = 12


@pytest.mark.parametrize(
    ["data", "expected_result"],
    [
        (
            (ID_, "upload", True, "success message", "some name"),
            {
                "file_name": "some name",
                "id": ID_,
                "action": "upload",
                "status": True,
                "message": "success message",
            },
        ),
        (
            (ID_, "delete", False, "error"),
            {
                "id": ID_,
                "action": "delete",
                "status": False,
                "message": "error",
            },
        ),
    ],
)
def test_to_obj(data, expected_result):
    assert to_obj(*data) == ActionResponse.parse_obj(expected_result)


def test_file_processor_is_extension_correct():
    mock_instance = FileProcessor(
        file=BytesIO(),
        bucket_storage="bucket_storage",
        session=Session(),
        storage=Minio("play.min.io"),
        file_key="some_file.pdf",
    )

    assert mock_instance.is_extension_correct() is True


def test_file_processor_is_extension_correct_without_extension():
    mock_instance = FileProcessor(
        file=BytesIO(),
        bucket_storage="bucket_storage",
        session=Session(),
        storage=Minio("play.min.io"),
        file_key="some_file",
    )

    assert mock_instance.is_extension_correct() is False


# @patch("assets.utils.common_utils.db.service.insert_file")
# def test_file_processor_is_inserted_to_database_file_inserted(
#     insert_file, pdf_file_bytes
# ):
#     file_processor = FileProcessor(
#         file=BytesIO(),
#         bucket_storage="bucket_storage",
#         session=Session(),
#         storage=Minio("play.min.io"),
#         file_key="some_file",
#     )
#     insert_file.return_value = True
#     file_processor.converted_file = pdf_file_bytes
#     assert file_processor.is_inserted_to_database()
#     insert_file.assert_called()


# @patch("assets.utils.common_utils.db.service.insert_file")
# def test_file_processor_is_inserted_to_database_file_not_inserted(
#     insert_file, pdf_file_bytes
# ):
#     file_processor = FileProcessor(
#         file=BytesIO(),
#         bucket_storage="bucket_storage",
#         session=Session(),
#         storage=Minio("play.min.io"),
#         file_key="some_file",
#     )
#     file_processor.converted_file = pdf_file_bytes
#     insert_file.return_value = False
#     assert file_processor.is_blank_is_created()
#     assert file_processor.is_inserted_to_database() is False
#     insert_file.assert_called()


@patch("assets.utils.minio_utils.upload_in_minio")
def test_file_processor_is_uploaded_to_storage_file_uploaded(upload_in_minio):
    file_processor = FileProcessor(
        file=BytesIO(),
        bucket_storage="bucket_storage",
        session=Session(),
        storage=Minio("play.min.io"),
        file_key="some_file",
    )
    upload_in_minio.return_value = True
    assert file_processor.is_uploaded_to_storage()
    upload_in_minio.assert_called()


@patch("assets.utils.common_utils.db.service.update_file_status")
@patch("assets.utils.minio_utils.upload_in_minio")
def test_file_processor_is_uploaded_to_storage_not_uploaded(
    upload_in_minio, update_file_status
):
    file_processor = FileProcessor(
        file=BytesIO(),
        bucket_storage="bucket_storage",
        session=Session(),
        storage=Minio("play.min.io"),
        file_key="some_file",
    )
    file_processor.new_file = SimpleNamespace(id=1)
    upload_in_minio.return_value = False
    update_file_status.return_value = None

    assert file_processor.is_uploaded_to_storage() is False
    upload_in_minio.assert_called()
    update_file_status.assert_called()


@patch("assets.utils.common_utils.db.service.update_file_status")
def test_file_processor_is_file_updated_status_updated(update_file_status):
    file_processor = FileProcessor(
        file=BytesIO(),
        bucket_storage="bucket_storage",
        session=Session(),
        storage=Minio("play.min.io"),
        file_key="some_file",
    )
    file_processor.new_file = SimpleNamespace(id=1)
    update_file_status.return_value = True

    assert file_processor.is_file_updated()
    update_file_status.assert_called()


@patch("assets.utils.common_utils.db.service.update_file_status")
def test_file_processor_is_file_updated_status_not_updated(update_file_status):
    file_processor = FileProcessor(
        file=BytesIO(),
        bucket_storage="bucket_storage",
        session=Session(),
        storage=Minio("play.min.io"),
        file_key="some_file",
    )
    file_processor.new_file = SimpleNamespace(id=1)
    update_file_status.return_value = False

    assert file_processor.is_file_updated() is False
    update_file_status.assert_called()


@patch("assets.utils.common_utils.FileProcessor.is_file_updated")
@patch("assets.utils.common_utils.FileProcessor.is_blank_is_created")
@patch(
    "assets.utils.common_utils.FileProcessor.is_original_file_uploaded_to_storage"  # noqa
)
@patch("assets.utils.common_utils.FileProcessor.is_uploaded_to_storage")
@patch("assets.utils.common_utils.FileProcessor.is_inserted_to_database")
@patch("assets.utils.common_utils.FileProcessor.is_converted_file")
@patch("assets.utils.common_utils.FileProcessor.is_extension_correct")
def test_file_processor_run_all_stages_passed(
    is_blank_is_created,
    is_extension_correct,
    is_converted_file,
    is_inserted_to_database,
    is_uploaded_to_storage,
    is_original_file_uploaded_to_storage,
    is_file_updated,
):
    file_processor = FileProcessor(
        file=BytesIO(),
        bucket_storage="bucket_storage",
        session=Session(),
        storage=Minio("play.min.io"),
        file_key="some_file",
    )

    is_blank_is_created.return_value = True
    is_extension_correct.return_value = True
    is_converted_file.return_value = True
    is_inserted_to_database.return_value = True
    is_uploaded_to_storage.return_value = True
    is_original_file_uploaded_to_storage.return_value = True
    is_file_updated.return_value = True

    assert file_processor.run()
    is_blank_is_created.assert_called()
    is_extension_correct.assert_called()
    is_converted_file.assert_called()
    is_inserted_to_database.assert_called()
    is_uploaded_to_storage.assert_called()
    is_original_file_uploaded_to_storage.assert_called()
    is_file_updated.assert_called()


@patch("assets.utils.common_utils.FileProcessor.is_file_updated")
@patch("assets.utils.common_utils.FileProcessor.is_uploaded_to_storage")
@patch("assets.utils.common_utils.FileProcessor.is_inserted_to_database")
@patch("assets.utils.common_utils.FileProcessor.is_extension_correct")
def test_file_processor_run_extension_check_failed(
    is_extension_correct,
    is_inserted_to_database,
    is_uploaded_to_storage,
    is_file_updated,
):
    file_processor = FileProcessor(
        file=BytesIO(),
        bucket_storage="bucket_storage",
        session=Session(),
        storage=Minio("play.min.io"),
        file_key="some_file",
    )

    is_extension_correct.return_value = False
    is_inserted_to_database.return_value = True
    is_uploaded_to_storage.return_value = True
    is_file_updated.return_value = True

    assert file_processor.run() is False
    is_extension_correct.assert_called()
    is_inserted_to_database.assert_not_called()
    is_uploaded_to_storage.assert_not_called()
    is_file_updated.assert_not_called()


@patch("assets.utils.common_utils.requests.post")
def test_file_processor_is_converted_file_converted(gotenberg, pdf_file_bytes):
    response = Response()
    response._content = pdf_file_bytes
    gotenberg.return_value = response
    with NamedTemporaryFile(suffix=".doc", prefix="some_file") as file:
        file_processor = FileProcessor(
            file=BytesIO(file.read()),
            bucket_storage="bucket_storage",
            session=Session(),
            storage=Minio("play.min.io"),
            file_key="some_file.doc",
        )
        assert file_processor.is_converted_file()


@patch("assets.utils.common_utils.get_mimetype")
@patch("assets.utils.common_utils.requests.post")
def test_file_processor_is_converted_file_conversion_error(
    gotenberg, get_mimetype, pdf_file_bytes
):
    response = Response()
    response._content = pdf_file_bytes
    gotenberg.return_value = response
    get_mimetype.return_value = "text/plain"
    with NamedTemporaryFile(suffix=".doc", prefix="some_file") as file:
        file_processor = FileProcessor(
            file=BytesIO(file.read()),
            bucket_storage="bucket_storage",
            session=Session(),
            storage=Minio("play.min.io"),
            file_key="some_file.doc",
        )
        file_processor.ext = ".doc"
        assert file_processor.is_converted_file() is False
        assert file_processor.conversion_status == "conversion error"


@patch("assets.utils.common_utils.requests.post")
@patch("assets.utils.common_utils.FileConverter.convert")
def test_file_processor_is_converted_file_conversion_not_in_formats(
    gotenberg, pdf_file_bytes
):
    response = Response()
    response._content = pdf_file_bytes
    gotenberg.return_value = response
    with NamedTemporaryFile(suffix=".doc", prefix="some_file") as file:
        file_processor = FileProcessor(
            file=BytesIO(file.read()),
            bucket_storage="bucket_storage",
            session=Session(),
            storage=Minio("play.min.io"),
            file_key="some_file.doc",
        )
        file_processor.ext = ".pdf"
        assert file_processor.is_converted_file() is True
        assert file_processor.conversion_status is None


# @patch("assets.utils.common_utils.FileProcessor.is_file_updated")
# @patch(
#     "assets.utils.common_utils.FileProcessor.is_original_file_uploaded_to_storage"
# )
# @patch("assets.utils.common_utils.FileProcessor.is_uploaded_to_storage")
# @patch("assets.utils.common_utils.FileProcessor.is_inserted_to_database")
# @patch("assets.utils.common_utils.FileProcessor.is_converted_file")
# @patch("assets.utils.common_utils.FileProcessor.is_extension_correct")
# def test_file_processor_run_database_insert_failed(
#     is_extension_correct,
#     is_converted_file,
#     is_inserted_to_database,
#     is_uploaded_to_storage,
#     is_original_file_uploaded_to_storage,
#     is_file_updated,
# ):
#     file_processor = FileProcessor(
#         file=BytesIO(),
#         bucket_storage="bucket_storage",
#         session=Session(),
#         storage=Minio("play.min.io"),
#         file_key="some_file",
#     )
#
#     is_extension_correct.return_value = True
#     is_converted_file.return_value = True
#     is_inserted_to_database.return_value = False
#     is_uploaded_to_storage.return_value = True
#     is_original_file_uploaded_to_storage.return_value = True
#     is_file_updated.return_value = True
#
#     assert file_processor.run() is False
#     is_extension_correct.assert_called()
#     is_converted_file.assert_called()
#     is_inserted_to_database.assert_called()
#     is_uploaded_to_storage.assert_not_called()
#     is_original_file_uploaded_to_storage.assert_not_called()
#     is_file_updated.assert_not_called()


# @patch("assets.utils.common_utils.FileProcessor.is_file_updated")
# @patch("assets.utils.common_utils.FileProcessor.is_uploaded_to_storage")
# @patch("assets.utils.common_utils.FileProcessor.is_inserted_to_database")
# @patch("assets.utils.common_utils.FileProcessor.is_extension_correct")
# def test_file_processor_run_storage_upload_failed(
#     is_extension_correct,
#     is_inserted_to_database,
#     is_uploaded_to_storage,
#     is_file_updated,
# ):
#     file_processor = FileProcessor(
#         file=BytesIO(),
#         bucket_storage="bucket_storage",
#         session=Session(),
#         storage=Minio("play.min.io"),
#         file_key="some_file",
#     )
#
#     is_extension_correct.return_value = True
#     is_inserted_to_database.return_value = True
#     is_uploaded_to_storage.return_value = False
#     is_file_updated.return_value = True
#
#     assert file_processor.run() is False
#     is_extension_correct.assert_called()
#     is_inserted_to_database.assert_called()
#     is_uploaded_to_storage.assert_called()
#     is_file_updated.assert_not_called()


# @patch("assets.utils.common_utils.FileProcessor.is_file_updated")
# @patch("assets.utils.common_utils.FileProcessor.is_uploaded_to_storage")
# @patch("assets.utils.common_utils.FileProcessor.is_inserted_to_database")
# @patch("assets.utils.common_utils.FileProcessor.is_extension_correct")
# def test_file_processor_run_status_update_failed(
#     is_extension_correct,
#     is_inserted_to_database,
#     is_uploaded_to_storage,
#     is_file_updated,
# ):
#     file_processor = FileProcessor(
#         file=BytesIO(),
#         bucket_storage="bucket_storage",
#         session=Session(),
#         storage=Minio("play.min.io"),
#         file_key="some_file",
#     )
#
#     is_extension_correct.return_value = True
#     is_inserted_to_database.return_value = True
#     is_uploaded_to_storage.return_value = True
#     is_file_updated.return_value = False
#
#     assert file_processor.run() is False
#     is_extension_correct.assert_called()
#     is_inserted_to_database.assert_called()
#     is_uploaded_to_storage.assert_called()
#     is_file_updated.assert_called()


def test_s3_manager_get_files():
    s3 = S3Manager("a", "b", endpoint_url=None)
    method = {"download_fileobj.return_value": None}
    s3.client = Mock(**method)

    file_keys = ["file_1.pdf", "file_2.png", "file_3.png"]

    files_dict = s3.get_files("some_s3_bucket", file_keys)
    for file_key in files_dict.keys():
        assert file_key in file_keys


@patch("assets.utils.s3_utils.S3Manager._check_bucket_exist")
@patch("assets.utils.s3_utils.S3Manager._check_files_exist")
def test_s3_manager_check_s3_buckets_and_files_exist(
    check_buckets, check_files
):
    s3 = S3Manager("a", "b", endpoint_url=None)
    check_buckets.return_value = None
    check_files.return_value = None
    assert s3.check_s3("some_bucket", ["file1", "file2"]) is None
    check_buckets.assert_called()
    check_files.assert_called()


@patch("assets.utils.s3_utils.S3Manager._check_bucket_exist")
@patch("assets.utils.s3_utils.S3Manager._check_files_exist")
def test_s3_manager_check_s3_buckets_not_exist(check_files, check_buckets):
    s3 = S3Manager("a", "b", endpoint_url=None)
    check_buckets.side_effect = BucketError
    check_files.return_value = None
    with pytest.raises(BucketError):
        s3.check_s3("some_bucket", ["file1", "file2"])
    check_buckets.assert_called()
    check_files.assert_not_called()


@patch("assets.utils.s3_utils.S3Manager._check_bucket_exist")
@patch("assets.utils.s3_utils.S3Manager._check_files_exist")
def test_s3_manager_check_s3_file_not_exist(check_files, check_buckets):
    s3 = S3Manager("a", "b", endpoint_url=None)
    check_buckets.return_value = None
    check_files.side_effect = FileKeyError
    with pytest.raises(FileKeyError):
        s3.check_s3("some_bucket", ["file1", "file2"])
    check_buckets.assert_called()
    check_files.assert_called()


def test_check_uploading_limit_exceed():
    uploading_list = list(map(str, range(settings.uploading_limit + 1)))
    with pytest.raises(UploadLimitExceedError):
        check_uploading_limit(uploading_list)


def test_check_uploading_limit_not_exceed():
    uploading_list = list(map(str, range(settings.uploading_limit - 1)))
    assert check_uploading_limit(uploading_list) is None


@patch("assets.utils.common_utils.get_mimetype")
@patch("assets.utils.common_utils.requests.post")
def test_file_processor_conversion_error(
    gotenberg, get_mimetype, pdf_file_bytes
):
    response = Response()
    response._content = pdf_file_bytes
    gotenberg.return_value = response
    get_mimetype.return_value = "text/plain"
    with NamedTemporaryFile(suffix=".doc", prefix="some_file") as file:
        new_db_file = FileObject()
        converter = FileConverter(
            file.read(), "some_file.doc", ".doc", "test", new_db_file
        )
        assert converter.convert() is False
        assert converter.conversion_status == "conversion error"


def test_convert_pdf(file_converter_service):
    with NamedTemporaryFile(suffix=".pdf", prefix="123") as tmp_file:
        tmp_file.write(b"sample_fetched_pdf_content")
        mock_path = PropertyMock(return_value=tmp_file.name)
        file_converter_service.new_file.id = 123
        with patch(
            "assets.utils.common_utils.FileConverter._tmp_file_name", mock_path
        ) as mock_:  # noqa
            file_converter_service.convert_pdf()
        assert file_converter_service.converted_ext == ".pdf"
        assert (
            file_converter_service.conversion_status
            == schemas.ConvertionStatus.CONVERTED_TO_PDF
        )
        file_converter_service.minio_client.fget_object.assert_called_once_with(  # noqa
            "sample_bucket_storage",
            "files/123/123.pdf",
            tmp_file.name,
        )


@patch("assets.utils.common_utils.get_mimetype")
@patch("assets.utils.common_utils.requests.post")
def test_file_converted_converted_to_pdf_side_effect(
    gotenberg, get_mimetype, pdf_file_bytes
):
    response = Response()
    response._content = pdf_file_bytes
    gotenberg.return_value = response
    get_mimetype.return_value = "text/plain"
    with NamedTemporaryFile(suffix=".doc", prefix="some_file") as file:
        new_db_file = FileObject()
        converter = FileConverter(
            file.read(), "some_file.doc", ".doc", "test", new_db_file
        )
        with pytest.raises(FileConversionError):
            converter.convert_to_pdf()
        assert converter.convert() is False
        assert converter.conversion_status == "conversion error"


def test_file_converted_converted_to_jpg(png_bytes):
    new_db_file = FileObject()
    converter = FileConverter(
        png_bytes, "some_file.png", ".png", "test", new_db_file
    )
    assert converter.convert() is True


def test_file_converted_converted_to_jpg_error(pdf_file_bytes):
    new_db_file = FileObject()
    converter = FileConverter(
        pdf_file_bytes, "some_file.png", ".png", "test", new_db_file
    )
    assert converter.convert() is False
    assert converter.conversion_status == "conversion error"


@pytest.mark.parametrize(
    ["data", "expected_result"],
    [
        ((1, 0), 1.0),
        ((0, 1), 1.0),
        ((-3, 1), 1.0),
        ((2, 1), 2.0),
        ((1, 2), 0.5),
    ],
)
def test_get_size_ratio(data, expected_result):
    assert minio_utils.get_size_ratio(*data) == expected_result


def test_thumb_size():
    m = create_autospec(Image)
    m.size = 1, 1
    assert minio_utils.thumb_size(m) == (settings.width, settings.width / 1)


def test_check_files_exist(minio_mock_exists_bucket_true):
    minio_mock_exists_bucket_true.list_objects.return_value = ("some.file",)
    assert minio_utils.check_file_exist(
        "some.file", "bucket", minio_mock_exists_bucket_true
    )


@pytest.mark.parametrize(
    ("bbox", "ext", "page_size", "expected_result"),
    [
        ((0, 0, 0, 0), 10, (100, 100), (0, 0, 10, 10)),
        ((10, 10, 10, 10), 50, (100, 200), (0, 0, 60, 60)),
        ((160, 200, 220, 300), 100, (250, 300), (60, 100, 250, 300)),
    ],
)
def test_extend_bbox(bbox, page_size, ext, expected_result):
    assert minio_utils.extend_bbox(bbox, page_size, ext) == expected_result


@pytest.mark.parametrize(
    ("file", "return_value", "expected_result"),
    [
        (b"", {"Page size": "595.28 x 841.89"}, (595.28, 841.89)),
        (b"", {"Page size": "220.09 x 900.01 pts"}, (220.09, 900.01)),
    ],
)
def test_get_pdf_page_size(file, return_value, expected_result):
    with patch(
        "assets.utils.minio_utils.pdf2image.pdfinfo_from_bytes",
        return_value=return_value,
    ):
        assert minio_utils.get_pdf_pts_page_size(file) == expected_result


def test_read_image():
    buffer = BytesIO()
    img = Image.new(mode="RGB", size=(10, 10))
    img.save(buffer, format="JPEG")
    img.close()
    assert minio_utils.read_image(buffer.getvalue())
    buffer.close()


@pytest.mark.parametrize(
    ("current_pixel_size", "original_pts_size", "bbox", "expected_result"),
    [
        (
            (1000.0, 2000.0),
            (500.0, 1000.0),
            (10.0, 10.0, 10.0, 10.0),
            (20.0, 20.0, 20.0, 20.0),
        ),
        (
            (700.0, 1400.0),
            (500.0, 700.0),
            (0.0, 200.0, 150.0, 0.0),
            (0.0, 400.0, 210.0, 0.0),
        ),
    ],
)
def test_get_pixel_bbox_size(
    current_pixel_size, original_pts_size, bbox, expected_result
):
    assert (
        minio_utils.get_pixel_bbox_size(
            current_pixel_size, original_pts_size, bbox
        )
        == expected_result
    )
