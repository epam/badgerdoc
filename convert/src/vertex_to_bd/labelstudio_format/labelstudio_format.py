import uuid
from pathlib import Path
from typing import List

from ..models.bd_annotation_model import BadgerdocAnnotation, Obj
from ..models.bd_tokens_model import BadgerdocToken, Page
from ..models.vertex_models import (
    Annotation,
    Data,
    LabelStudioModel,
    ModelItem,
    ResultItem,
    Value,
)


class LabelStudioFormat:
    # TODO: support more than 1 page
    def __init__(self) -> None:
        self.labelstudio_data = LabelStudioModel()

    def from_badgerdoc(
        self,
        badgerdoc_tokens: Page,
        badgerdoc_annotations: BadgerdocAnnotation,
    ):
        text = "".join([obj.text for obj in badgerdoc_tokens.objs])
        item = ModelItem(
            data=Data(text=text),
        )
        self.labelstudio_data.__root__.append(item)

    def export_json(self, path: Path):
        path.write_text(self.labelstudio_data.json())
