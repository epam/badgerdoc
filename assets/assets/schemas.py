import datetime
import enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from assets.db.models import Datasets


class MinioObjects(BaseModel):
    objects: List[int]


class Dataset(BaseModel):
    name: str
    id: Optional[int] = Field(default=None)


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
    extension: Optional[str] = None
    original_ext: Optional[str] = None
    content_type: str
    pages: Optional[int] = None
    last_modified: datetime.datetime
    status: FileProcessingStatus
    path: str
    datasets: List[Dataset]
    model_config = ConfigDict(from_attributes=True)

    @field_validator("datasets", mode="before")
    @classmethod
    def validate_datasets(  # pylint: disable=E0213
        cls, v: Optional[List[Datasets]]
    ) -> List[dict]:
        if not v:
            return []
        return [{"id": el.id, "name": el.name} for el in v]


class DatasetResponse(BaseModel):
    id: int
    name: str
    count: Optional[int] = None
    created: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class AssociationResponse(BaseModel):
    dataset_name: str
    file_id: int


class ActionResponse(BaseModel):
    file_name: Optional[str] = None
    id: Optional[int] = None
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


class ExtractionBase(BaseModel):
    file_id: int
    engine: str


class ExtractionResponse(ExtractionBase):
    id: int
    file_id: int
    file_extension: str
    file_path: str
    status: str

    class Config:
        orm_mode = True
