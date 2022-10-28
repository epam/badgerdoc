import enum
from typing import Any, Dict, List


class TempEnum(str, enum.Enum):
    pass


def get_mapping_fields(index_settings: Dict[str, Any]) -> Dict[str, Any]:
    properties = index_settings["mappings"]["properties"]
    return properties


def enum_generator(fields: List[str], class_name: str) -> TempEnum:
    enum_fields = {key.upper(): key for key in fields}
    model = TempEnum(class_name, enum_fields)  # type: ignore
    return model
