import uuid
from datetime import datetime

import pytest
from sqlalchemy import INTEGER, VARCHAR, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID

from annotation.annotations.main import row_to_dict
from annotation.database import Base


class AnnotationRow:
    def __init__(
        self,
        uuid_attr: uuid.UUID,
        datetime_attr: datetime,
        str_attr: str,
        int_attr: int,
    ):
        self.uuid_attr = uuid_attr
        self.datetime_attr = datetime_attr
        self.str_attr = str_attr
        self.int_attr = int_attr


class AnnotationRowTable(Base):
    __tablename__ = "test"

    uuid_attr = Column(UUID(as_uuid=True), primary_key=True)
    datetime_attr = Column(DateTime())
    str_attr = Column(VARCHAR)
    int_attr = Column(INTEGER)


SPECIFIC_DATE_TIME = datetime(2024, 1, 1, 10, 10, 0)

ANNOTATION_ROW = AnnotationRow(
    uuid_attr=uuid.UUID("34c665fd-ddfb-412c-a3f8-3351d87c6030"),
    datetime_attr=SPECIFIC_DATE_TIME,
    str_attr="test string",
    int_attr=1,
)


ANNOTATION_ROW_TABLE = AnnotationRowTable(
    uuid_attr="34c665fd-ddfb-412c-a3f8-3351d87c6030",
    datetime_attr=SPECIFIC_DATE_TIME,
    str_attr="test string",
    int_attr=1,
)


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "row",
        "expected_dictionary",
    ],
    [
        (
            ANNOTATION_ROW_TABLE,
            {
                "uuid_attr": "34c665fd-ddfb-412c-a3f8-3351d87c6030",
                "datetime_attr": "2024-01-01T10:10:00",
                "str_attr": "test string",
                "int_attr": 1,
            },
            # row_to_dict won't cast INTEGER to string
        ),
        (
            ANNOTATION_ROW,
            {
                "uuid_attr": "34c665fd-ddfb-412c-a3f8-3351d87c6030",
                "datetime_attr": "2024-01-01T10:10:00",
                "str_attr": "test string",
                "int_attr": 1,
            },
            # it return the same as the previous case
        ),
    ],
)
def test_row_to_dict(row, expected_dictionary):
    result = row_to_dict(row)
    print(result)
    assert result == expected_dictionary
