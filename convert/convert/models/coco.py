from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List

from pydantic import BaseModel, Field


class Info(BaseModel):
    year: int = datetime.now().year
    version: str = Field(description="Version of the dataset")
    description: str = Field(
        default=f"This dataset was created by BadgerDoc team in {datetime.now().year}",
        description="The description of the dataset",
    )
    contributor: str = "EPAM Systems, BadgerDoc"
    url: str = Field(default="kb.epam.com/display/EPMUII/BadgerDoc")
    date_created: datetime = Field(default_factory=datetime.now)


class BBox(List[int]):
    """The COCO bounding box format is
    [
        top left x position,
        top left y position,
        width,
        height
    ]
    """

    def __init__(self, iterable: Iterable[Any]) -> None:
        try:
            tmp = tuple((float(val) for val in iterable))
        except TypeError as err:
            raise ValueError(
                "Bounding box should contains only numeric values"
            ) from err
        if len(tmp) != 4:
            raise ValueError("Bounding box must contains x, y, width and height")
        super().__init__()


class Image(BaseModel):
    id: int = Field(gt=0)
    height: int = Field(gt=0, title="The height of the image")
    width: int = Field(gt=0, title="The width of the image")
    file_name: Path = Field(title="Name of file in the ... folder")  # TODO


class Licenses(BaseModel):
    id: int = Field(gt=0)
    name: str
    url: str


class Category(BaseModel):
    id: int = Field(gt=0)
    name: str
    supercategory: str


class Annotation(BaseModel):
    id: int = Field(gt=0)
    image_id: int
    category_id: str
    bbox: BBox
    area: float
    isbbox: bool


class CocoDataset(BaseModel):
    annotations: List[Annotation]
    images: List[Image]
    categories: List[Category]


class ImportJobCreatedSuccess(BaseModel):
    msg: str = Field(example="Import job is created")
    job_id: int


class ExportInputData(BaseModel):
    job_lst: List[int]
    export_format: str
    validated_only: bool = Field(default=False)


class ExportConvertStart(BaseModel):
    url: str
    bucket: str
    minio_path: str
    msg: str = Field(example="Conversion is started")


class SuccessConvertFromCoco(BaseModel):
    msg: str = Field(example="Coco dataset was converted to badgerdoc format")


class SuccessConvertToCoco(BaseModel):
    msg: str = Field(default="Dataset was converted to coco format")


class WrongConvertToCoco(BaseModel):
    details: str = Field(example="Not existing annotation file")


class UnavailableService(BaseModel):
    details: str = Field(example="Service is unavailable")


class WrongConvertFromCoco(BaseModel):
    details: str = Field(example="Not existing dataset")


class DataS3(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    bucket_s3: str
    files_keys: List[str]


class UnfinishedConversion(BaseModel):
    msg: str = Field(example="Conversion is not finished yet")
