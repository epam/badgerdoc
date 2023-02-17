from typing import Any, Dict, Optional, Tuple

from assets.db.models import Association, Datasets, FileObject, SessionLocal
from assets.logger import get_logger
from assets.schemas import FileProcessingStatusForUpdate
from filter_lib import PaginationParams, form_query, map_request_to_filter
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, load_only, selectinload

logger = get_logger(__name__)


def session_scope_for_dependency() -> Session:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def insert_file(
    session: Session,
    file: str,
    bucket_name: str,
    size: int,
    ext: str,
    original_ext: str,
    content_type: str,
    pages: Optional[int],
    file_status: str,
) -> Optional[FileObject]:
    new_file = FileObject(
        original_name=file,
        bucket=bucket_name,
        size_in_bytes=size,
        extension=ext,
        original_ext=original_ext,
        content_type=content_type,
        pages=pages,
        status=file_status,
    )
    try:
        session.add(new_file)
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Error while inserting into db, detail: {e}")
        session.rollback()
        return None
    return new_file


def update_file(
    file_id: int,
    session: Session,
    file_to_update: str,
    bucket_name: str,
    size: int,
    ext: str,
    original_ext: str,
    content_type: str,
    pages: Optional[int],
    file_status: str,
) -> Optional[FileObject]:
    file: Optional[FileObject] = (
        session.query(FileObject).filter(FileObject.id == file_id).with_for_update()
    ).first()
    file.original_name = file_to_update
    file.bucket = (bucket_name,)
    file.size_in_bytes = size
    file.content_type = content_type
    file.extension = ext
    file.original_ext = original_ext
    file.pages = pages
    file.status = file_status
    try:
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Error while updating file - detail: {e}")
        session.rollback()
        return None
    return file


def insert_dataset(session: Session, dataset_name: str) -> None:
    ds = Datasets(name=dataset_name)
    session.add(ds)
    session.commit()


def delete_file_from_db(session: Session, row_id: int) -> Any:
    q = session.query(FileObject).filter(FileObject.id == row_id).with_for_update()
    decrease_count_in_bounded_datasets(session, row_id)
    res = q.delete()
    session.commit()
    return res


def delete_dataset_from_db(session: Session, ds_name: str) -> Any:
    res = session.query(Datasets).filter(Datasets.name == ds_name).delete()
    session.commit()
    return res


def update_file_status(
    file_id: int, file_status: FileProcessingStatusForUpdate, session: Session
) -> Optional[FileObject]:
    file: Optional[FileObject] = (
        session.query(FileObject).filter(FileObject.id == file_id).with_for_update()
    ).first()
    file.status = file_status
    try:
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Error while updating file status - detail: {e}")
        session.rollback()
        return None
    return file


def get_file_by_id(session: Session, file_id: int) -> Optional[FileObject]:
    return session.query(FileObject).get(file_id)


def get_dataset_by_name(session: Session, name: str) -> Optional[Datasets]:
    return session.query(Datasets).filter(Datasets.name == name).first()


def get_all_files_query(
    session: Session, request: Dict[str, Any]
) -> Tuple[Query, PaginationParams]:
    filter_args = map_request_to_filter(request, "FileObject")
    query = session.query(FileObject).options(selectinload(FileObject.datasets))
    query, pag = form_query(filter_args, query)
    return query, pag


def get_all_datasets_query(
    session: Session, request: Dict[str, Any]
) -> Tuple[Query, PaginationParams]:
    filter_args = map_request_to_filter(request, "Datasets")
    query = session.query(Datasets)
    query, pag = form_query(filter_args, query)
    return query, pag


def get_files_in_dataset_query(
    session: Session, dataset: str, request: Dict[str, Any]
) -> Tuple[Query, PaginationParams]:
    filter_args = map_request_to_filter(request, "FileObject")
    query = (
        session.query(FileObject)
        .options(selectinload(FileObject.datasets))
        .join(Association, Datasets)
        .filter(Datasets.name == dataset)
    )
    query, pag = form_query(filter_args, query)
    return query, pag


def get_all_bonds_query(
    session: Session, request: Dict[str, Any]
) -> Tuple[Query, PaginationParams]:
    filter_args = map_request_to_filter(request, "Association")
    query = session.query(Datasets, FileObject, Association).filter(
        FileObject.id == Association.file_id,
        Datasets.id == Association.dataset_id,
    )
    query, pag = form_query(filter_args, query)
    return query, pag


def is_bounded(session: Session, file_id: int, ds_name: str) -> Optional[FileObject]:
    bond = (
        session.query(FileObject)
        .join(Association, Datasets)
        .options(load_only(FileObject.id))
        .filter(FileObject.id == file_id, Datasets.name == ds_name)
        .first()
    )
    return bond


def add_dataset_to_file(session: Session, file: FileObject, ds: Datasets) -> None:
    ds_query = session.query(Datasets).filter(Datasets.id == ds.id).with_for_update()
    file_obj = (
        session.query(FileObject)
        .filter(FileObject.id == file.id)
        .with_for_update()
        .first()
    )
    ds_obj = ds_query.first()
    file_obj.datasets.append(ds_obj)
    ds_query.update({Datasets.count: Datasets.count + 1})
    session.commit()


def remove_dataset_from_file(session: Session, file: FileObject, ds: Datasets) -> None:
    ds_query = session.query(Datasets).filter(Datasets.id == ds.id).with_for_update()
    file_obj = (
        session.query(FileObject)
        .filter(FileObject.id == file.id)
        .with_for_update()
        .first()
    )
    ds_obj = ds_query.first()
    file_obj.datasets.remove(ds_obj)
    ds_query.update({Datasets.count: Datasets.count - 1})
    session.commit()


def decrease_count_in_bounded_datasets(session: Session, file_id: int) -> None:
    query = (
        session.query(Datasets.id)
        .join(FileObject.datasets)
        .filter(FileObject.id == file_id)
    )
    ds_ids = [row.id for row in query]
    session.query(Datasets).filter(Datasets.id.in_(ds_ids)).with_for_update().update(
        {Datasets.count: Datasets.count - 1}, synchronize_session="fetch"
    )
    session.commit()


def get_all_files_by_ds_id(session: Session, ds_id: int) -> Query:
    query = (
        session.query(FileObject)
        .options(selectinload(FileObject.datasets))
        .join(Association, Datasets)
        .filter(Datasets.id == ds_id)
    )
    return query


def get_dataset_by_id(session: Session, ds_id: int) -> Optional[Datasets]:
    return session.query(Datasets).get(ds_id)
