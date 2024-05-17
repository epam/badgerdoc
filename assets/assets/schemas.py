import datetime
import enum
from typing import List, Optional

from pydantic import BaseModel, validator

from assets.db.models import Datasets


class MinioObjects(BaseModel):
    objects: List[int]


class Dataset(BaseModel):
    name: str


class Bucket(Dataset):
    pass


class FilesToDataset(Dataset):
    objects: List[int]


class ConvertionStatus(str, enum.Enum):
    ERROR = ("conversion error",)
    CONVERTED_TO_PDF = ("converted to PDF",)
    CONVERTED_TO_JPG = "converted to JPEG"


class FileProcessingStatus(str, enum.Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PREPROCESSING_IN_PROGRESS = "preprocessing in progress"
    PREPROCESSED = "preprocessed"
    FAILED = "failed"


class FileProcessingStatusForUpdate(str, enum.Enum):
    PREPROCESSING_IN_PROGRESS = "preprocessing in progress"
    PREPROCESSED = "preprocessed"
    FAILED = "failed"


class FileResponse(BaseModel):
    id: int
    original_name: str
    bucket: str
    size_in_bytes: int
    extension: Optional[str]
    original_ext: Optional[str]
    content_type: str
    pages: Optional[int]
    last_modified: datetime.datetime
    status: FileProcessingStatus
    path: str
    datasets: List[str]

    class Config:
        orm_mode = True

    @validator("datasets", pre=True)
    def validate_datasets(  # pylint: disable=E0213
        cls, v: Optional[List[Datasets]]
    ) -> List[str]:
        if not v:
            return []
        return [el.name for el in v]


class DatasetResponse(BaseModel):
    id: int
    name: str
    count: Optional[int]
    created: datetime.datetime

    class Config:
        orm_mode = True


class AssociationResponse(BaseModel):
    dataset_name: str
    file_id: int


class ActionResponse(BaseModel):
    file_name: Optional[str] = None
    id: Optional[int]
    action: str
    status: bool
    message: str


class PreprocessResponse(BaseModel):
    file: int
    status: FileProcessingStatusForUpdate


class S3Data(BaseModel):
    access_key_id: str
    secret_access_key: str
    bucket_s3: str
    files_keys: List[str]
