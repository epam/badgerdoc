import os
import tempfile
from io import BytesIO
from typing import Optional, Tuple, Union

import fastapi
import minio.error
import pdf2image.exceptions
import PIL.Image
import urllib3.exceptions
from badgerdoc_storage import storage as bd_storage

from assets import db, exceptions, logger
from assets.config import settings
from assets.utils import chem_utils

logger_ = logger.get_logger(__name__)


class NotConfiguredException(Exception):
    pass


def upload_in_minio(
    storage: bd_storage.BadgerDocStorage,
    file: bytes,
    file_obj: db.models.FileObject,
) -> bool:
    """
    Uploads file and its thumbnail into Minio
    """
    pdf_bytes = make_thumbnail_pdf(file)
    if pdf_bytes and isinstance(pdf_bytes, bytes):
        upload_thumbnail(
            storage=storage,
            stream=pdf_bytes,
            path=file_obj.thumb_path,
        )

    image_bytes = make_thumbnail_images(file)
    if image_bytes and isinstance(image_bytes, bytes):
        upload_thumbnail(
            storage=storage, stream=image_bytes, path=file_obj.thumb_path
        )
    return put_file_to_minio(
        file, file_obj, file_obj.content_type, "converted", storage.tenant
    )


def remake_thumbnail(file_obj: db.models.FileObject, tenant: str) -> bool:
    storage = bd_storage.get_storage(tenant)
    with tempfile.TemporaryDirectory() as t_path:
        f_path = os.path.join(t_path, "file")
        try:
            storage.download(file_obj.path, f_path)
        except bd_storage.BadgerDocStorageError:
            logger_.warning("Original file %s was not found", file_obj.path)
            return False
        with open(f_path, "rb") as obj:
            file_data = obj.read()
    ext = file_obj.extension
    logger_.debug("Generate thumbnail from extension: %s", ext)

    if ext not in chem_utils.SUPPORTED_FORMATS:
        raise exceptions.AssetsUnsupportedFileFormat(
            "File extension %s is not supported", ext
        )

    if "chem" == chem_utils.SUPPORTED_FORMATS[ext]:
        file_bytes = chem_utils.make_thumbnail(file_data, ext)
    elif "pdf" == chem_utils.SUPPORTED_FORMATS[ext]:
        file_bytes = make_thumbnail_pdf(file_data)
    else:
        logger_.error("Unable to create thumbnail, unsupported extension")
        return False

    if file_bytes and isinstance(file_bytes, bytes):
        upload_thumbnail(storage, file_bytes, file_obj.thumb_path)
    image_bytes = make_thumbnail_images(obj.data)
    if image_bytes and isinstance(image_bytes, bytes):
        upload_thumbnail(storage, image_bytes, file_obj.thumb_path)
    if not file_bytes and not image_bytes:
        logger_.error("File is not an image")
        return False
    logger_.info("Successfully created thumbnail for %s", file_obj.path)
    return True


def make_pdf_piece(
    file_obj: db.models.FileObject,
    page_number: int,
    bbox: Tuple[float, float, float, float],
    piece_path: str,
    storage: minio.Minio,
) -> bool:
    obj: urllib3.response.HTTPResponse = storage.get_object(
        file_obj.bucket, file_obj.path
    )
    try:
        img = read_pdf_page(obj.data, page_number)
        if img is None:
            logger_.error(
                "Can't convert file <id %s, bucket %s>}",
                file_obj.id,
                file_obj.bucket,
            )
            return False

        pdf_pts_size = get_pdf_pts_page_size(obj.data)
        pixel_bbox = get_pixel_bbox_size(img.size, pdf_pts_size, bbox)
        bbox_extended = extend_bbox(pixel_bbox, img.size, settings.bbox_ext)
        cropped = img.crop(bbox_extended)
        target_size = thumb_size(cropped)
        buf = BytesIO()
        cropped.resize(target_size).save(buf, quality=100, format="JPEG")
        img.close()
        byte_im = buf.getvalue()
        upload_thumbnail(file_obj.bucket, byte_im, storage, piece_path)
        logger_.info("Successfully uploaded %s", piece_path)
        buf.close()
    finally:
        obj.close()
        obj.release_conn()
    return True


def get_pdf_pts_page_size(pdf_bytes: bytes) -> Tuple[float, float]:
    info = pdf2image.pdfinfo_from_bytes(pdf_bytes)
    page_info = info.get("Page size", "595.28 x 841.89")
    _s = page_info.strip().split()
    size = tuple(map(float, (_s[0], _s[2])))
    return size  # type: ignore


def put_file_to_minio(
    file: bytes,
    file_obj: db.models.FileObject,
    content_type: str,
    folder: str,
    tenant: str,
) -> bool:
    paths = {"origin": file_obj.origin_path, "converted": file_obj.path}
    storage_ = bd_storage.get_storage(tenant)
    try:
        storage_.upload_obj(
            paths[folder],
            BytesIO(file),
            content_type=content_type,
        )
    except urllib3.exceptions.MaxRetryError as e:
        logger_.error(f"Connection error - detail: {e}")
        return False
    logger_.info(f"File {file_obj.original_name} successfully uploaded")
    return True


def read_pdf_page(
    file: bytes, page_number: int = 1, dpi: int = 200
) -> Optional[PIL.Image.Image]:
    try:
        img = pdf2image.convert_from_bytes(
            file,
            first_page=page_number,
            last_page=page_number,
            dpi=dpi,
        )[0]
    except pdf2image.exceptions.PDFPageCountError:
        return None
    return img


def bytes_to_file(file_bytes, output_file):
    with open(output_file, "wb") as file:
        file.write(file_bytes)


def read_image(file: bytes) -> Optional[PIL.Image.Image]:
    try:
        img = PIL.Image.open(BytesIO(file))
    except PIL.UnidentifiedImageError:
        return None
    return img


def make_thumbnail_pdf(file: bytes) -> Union[bool, bytes]:
    buf = BytesIO()
    img = read_pdf_page(file, page_number=1)
    if img is None:
        return False
    size = thumb_size(img)
    img.thumbnail(size)
    img.save(buf, format="JPEG")
    img.close()
    byte_im = buf.getvalue()
    return byte_im


def make_thumbnail_images(file: bytes) -> Union[bool, bytes]:
    buf = BytesIO()
    img = read_image(file)
    if img is None:
        return False
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    size = thumb_size(img)
    img.thumbnail(size)
    img.save(buf, "JPEG")
    img.close()
    byte_im = buf.getvalue()
    return byte_im


def upload_thumbnail(
    storage: bd_storage.BadgerDocStorage,
    stream: bytes,
    path: str,
    content_type: str = "image/jpeg",
) -> bool:
    streamed = BytesIO(stream)
    try:
        storage.upload_obj(
            target_path=path,
            file=streamed,
            content_type=content_type,
        )
    except urllib3.exceptions.MaxRetryError as e:
        logger_.error(f"Connection error - detail: {e}")
        return False
    logger_.info("Thumbnail %s uploaded", path)
    return True


def delete_one_from_minio(bucket: str, obj: str, client: minio.Minio) -> bool:
    try:
        objects = client.list_objects(bucket, obj, recursive=True)
        names = [a.object_name for a in objects]
        if not names:
            logger_.error(f"{obj} does not exist in bucket {bucket}")
            return False
        for name in names:
            client.remove_object(bucket, name)
    except urllib3.exceptions.MaxRetryError as e:
        logger_.error(f"Connection error - detail: {e}")
        return False
    except minio.S3Error as e:
        logger_.error(f"S3 error - detail: {e}")
        return False
    logger_.info(f"Object {obj} successfully removed")
    return True


def stream_minio(
    path: str, bucket: str, storage: minio.Minio
) -> urllib3.response.HTTPResponse:
    try:
        response = storage.get_object(bucket, path)
    except urllib3.exceptions.MaxRetryError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except minio.S3Error as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"{str(e.message)}",
        )
    return response  # type: ignore


def check_file_exist(path: str, bucket: str) -> bool:
    storage = bd_storage.get_storage(bucket)
    return storage.exists(path)


def close_conn(conn: urllib3.response.HTTPResponse) -> None:
    """
    Closes connection after returning response
    Args:
        conn: urllib3.response.HTTPResponse

    """
    conn.close()
    conn.release_conn()


def get_size_ratio(width: int, height: int) -> float:
    try:
        r = width / height
        if r <= 0:
            logger_.error(
                "Current size raio <= 0! w = %s , h = %s", width, height
            )
            r = 1.0
        return r
    except ZeroDivisionError:
        logger_.error("Height of image is 0")
        return 1.0


def thumb_size(img: PIL.Image.Image) -> Tuple[int, int]:
    ratio = get_size_ratio(*img.size)
    height = settings.width / ratio
    return settings.width, int(height)


def get_pixel_bbox_size(
    pixel_size: Tuple[float, float],
    pts_size: Tuple[float, float],
    bbox: Tuple[float, float, float, float],
) -> Tuple[float, float, float, float]:
    width_multiplier = round(pixel_size[0] / pts_size[0], 2)
    height_multiplier = round(pixel_size[1] / pts_size[1], 2)
    return (
        bbox[0] * width_multiplier,
        bbox[1] * height_multiplier,
        bbox[2] * width_multiplier,
        bbox[3] * height_multiplier,
    )


def extend_bbox(
    bbox: Tuple[float, float, float, float],
    page_size: Tuple[float, float],
    ext: int,
) -> Tuple[int, int, int, int]:
    w_1 = int(max(bbox[0] - ext, 0))
    h_1 = int(max(bbox[1] - ext, 0))
    w_2 = int(min(bbox[2] + ext, page_size[0]))
    h_2 = int(min(bbox[3] + ext, page_size[1]))
    return w_1, h_1, w_2, h_2


def check_bucket(*args, **kwargs):
    raise NotImplementedError()
