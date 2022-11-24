# flake8: noqa: F501
from typing import Any, Dict, List, Optional, Union

import fastapi
import filter_lib
import sqlalchemy.exc
import sqlalchemy.orm
import sqlalchemy_filters.exceptions

from src import db, schemas

router = fastapi.APIRouter(prefix="/datasets", tags=["datasets"])


@router.post(
    "/search",
    response_model=Union[filter_lib.Page[schemas.DatasetResponse], filter_lib.Page[Any]],  # type: ignore
    name="searches for datasets",
)
async def search_datasets(
    request: db.models.DatasetRequest,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> filter_lib.Page[schemas.DatasetResponse]:
    """
    Allows getting datasets data with filters, sorts and pagination.

        Args:\n
            request: a request to get datasets data, schema for this request
            generated automatically.

        Returns:\n
            an array of datasets data

    """
    try:
        query, pag = db.service.get_all_datasets_query(session, request.dict())
    except sqlalchemy_filters.exceptions.BadFilterFormat as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Wrong params for operation. Hint: check types. Params = {e.args}",
        )
    return filter_lib.paginate([row for row in query], pag)


@router.post(
    "", status_code=fastapi.status.HTTP_201_CREATED, name="creates new dataset"
)
async def create_dataset(
    item: schemas.Dataset,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> Dict[str, Any]:
    """
    Creates a new dataset object in database. If dataset with given name is already exists
    then HTTPException 400 will be raised.

        Args:\n
            item: dataset model, has only "name" field which is str

        Returns:\n
            a message with a result of creating a dataset

        Raises:\n
            HTTPException 400 if dataset already exists

    """
    try:
        db.service.insert_dataset(session, item.name)
    except sqlalchemy.exc.IntegrityError:
        session.rollback()
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset {item.name} already exists!",
        )
    except sqlalchemy.exc.SQLAlchemyError as e:
        session.rollback()
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Bad request {e.args}",
        )
    return {"detail": f"Dataset {item.name} successfully created!"}


@router.delete(
    "",
    status_code=fastapi.status.HTTP_201_CREATED,
    name="removes dataset by its name",
)
async def delete_dataset(
    item: schemas.Dataset,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> Dict[str, Any]:
    """
    Deletes a dataset with a given name from a database. If that dataset does not exist
    in a database, then  HTTPException 404 will be raised.

        Args:\n
            item: dataset model, has only "name" field which is str

        Returns:\n
            a message with a result of removing a dataset

        Raises:\n
            HTTPException 404 if dataset does not exist

    """
    res = db.service.delete_dataset_from_db(session, item.name)
    if not res:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {item.name} does not exist!",
        )
    return {"detail": f"Dataset {item.name} successfully deleted!"}


@router.post(
    "/{dataset}/files/search",
    response_model=Union[filter_lib.Page[schemas.FileResponse], filter_lib.Page[Any]],  # type: ignore
    name="searches for files inside selected dataset",
)
async def get_files_by_dataset(
    dataset: str,
    request: db.models.FileRequest,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> filter_lib.Page[schemas.FileResponse]:
    """
    Takes a dataset name and returns all files metadata with this dataset.
    Every object will be represented as dict.
    If dataset with that doesn't exist HTTPException 404 will be raised.

        Args:\n
            dataset: str name of a Dataset's object

        Returns:\n
            List of metadata for all files that have relation
            with provided dataset.

        Raises:\n
            HTTPException 404 if dataset doesn't exist

    """
    ds = db.service.get_dataset_by_name(session, dataset)
    if not ds:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset} does not exist!",
        )
    try:
        query, pag = db.service.get_files_in_dataset_query(
            session, dataset, request.dict()
        )
    except sqlalchemy_filters.exceptions.BadFilterFormat as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Wrong params for operation. Hint: check types. Params = {e.args}",
        )
    return filter_lib.paginate([row for row in query], pag)


@router.get(
    "/{dataset_id}/files",
    response_model=List[schemas.FileResponse],
    name="get all files by dataset id",
)
def get_all_files_by_dataset_id(
    dataset_id: int,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> Optional[List[schemas.FileResponse]]:
    if not db.service.get_all_files_by_ds_id(session, dataset_id):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with id {dataset_id} does not exist!",
        )
    query = db.service.get_all_files_by_ds_id(session, dataset_id)
    return [row for row in query]
