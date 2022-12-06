# flake8: noqa: F501
from typing import Any, Dict, List, Optional

import fastapi
import filter_lib
import sqlalchemy.orm

from src import db, schemas, utils

router = fastapi.APIRouter(prefix="/datasets/bonds", tags=["bonds"])


@router.post(
    "/search",
    response_model=filter_lib.Page[schemas.AssociationResponse],
    name="gets pairs Dataset Name - File Id",
)
async def search_bonds(
    request: filter_lib.BaseSearch,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> filter_lib.Page[Dict[str, Any]]:
    """
    Takes every bounded pair dataset-file and returns them.

        Args:\n
            request: a request to get bonds with a pagination.

        Returns:\n
            an array of bonds dataset-file

    """
    query, pag = db.service.get_all_bonds_query(session, request.dict())
    return filter_lib.paginate(
        [{"dataset_name": el[0].name, "file_id": el[1].id} for el in query],
        pag,
    )


@router.post(
    "",
    status_code=fastapi.status.HTTP_201_CREATED,
    response_model=List[schemas.ActionResponse],
    name="bounds array of files to a dataset",
)
async def bound_files_to_dataset(
    item: schemas.FilesToDataset,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> List[schemas.ActionResponse]:
    """
    Bounds file objects to a given dataset. If dataset does not exist HTTPException
    404 will be raised. For each file result will be written into resulting dict.
    If file doesn't exist or already bounded to that dataset it will be skipped.

        Args:\n
            name: str name of a dataset
            objects: list of file ids


        Returns:\n
            Array that contains result of bounding for each element

        Raises:\n
            HTTPException 404 if dataset does not exist

    """
    ds = db.service.get_dataset_by_name(session, item.name)
    if not ds:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {item.name} does not exist!",
        )

    action = "bound"
    result: List[schemas.ActionResponse] = []
    for file_id in item.objects:
        obj = db.service.get_file_by_id(session, file_id)
        if not obj:
            result.append(
                utils.common_utils.to_obj(
                    file_id, action, False, "File does not exist!"
                )
            )
            continue

        bounded = db.service.is_bounded(session, file_id, item.name)
        if bounded:
            result.append(
                utils.common_utils.to_obj(
                    file_id,
                    action,
                    False,
                    f"File {obj.original_name} already bounded with dataset {item.name}",
                    obj.original_name,
                )
            )
            continue

        db.service.add_dataset_to_file(session, obj, ds)
        result.append(
            utils.common_utils.to_obj(
                file_id,
                action,
                True,
                f"Successfully bounded dataset {ds.name} with file {obj.original_name}",
                obj.original_name,
            )
        )

    return result


@router.delete(
    "",
    status_code=fastapi.status.HTTP_201_CREATED,
    response_model=List[schemas.ActionResponse],
    name="removes array of files from dataset",
)
async def unbound_files_from_dataset(
    item: schemas.FilesToDataset,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> List[schemas.ActionResponse]:
    """
    Unbound file objects with a given dataset. If dataset does not exist HTTPException
    404 will be raised. For each file result will be written into resulting dict.
    If file doesn't exist or not bounded to that dataset it will be skipped.

        Args:\n
            item: FilesToDataset model that contains:
                objects: list of file ids
                name: str name of a dataset

        Returns:\n
            Array that contains result of un-bounding for each element

        Raises:\n
            HTTPException 404 if dataset does not exist

    """
    ds = db.service.get_dataset_by_name(session, item.name)
    if not ds:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {item.name} does not exist!",
        )

    action = "unbound"
    result: List[schemas.ActionResponse] = []
    for file_id in item.objects:
        obj = db.service.get_file_by_id(session, file_id)
        if not obj:
            result.append(
                utils.common_utils.to_obj(
                    file_id, action, False, "File does not exist!"
                )
            )
            continue
        bounded = db.service.is_bounded(session, file_id, item.name)
        if not bounded:
            result.append(
                utils.common_utils.to_obj(
                    file_id,
                    action,
                    False,
                    f"File {obj.original_name} is not bounded with dataset {item.name}",
                    obj.original_name,
                )
            )
            continue
        db.service.remove_dataset_from_file(session, bounded, ds)
        result.append(
            utils.common_utils.to_obj(
                file_id,
                action,
                True,
                f"Successfully unbounded dataset {ds.name} with file {obj.original_name}",
                obj.original_name,
            )
        )

    return result
