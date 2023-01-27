from pathlib import Path
from typing import List

from ..models.bd_annotation_model import AnnotationLink, BadgerdocAnnotation
from ..models.bd_tokens_model import BadgerdocToken, Page
from ..models.label_studio_models import (
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
        objs = self.convert_annotation_from_bd(
            badgerdoc_annotations, badgerdoc_tokens.objs
        )
        relations = self.convert_relation_from_bd(
            badgerdoc_annotations, badgerdoc_tokens.objs
        )
        item = ModelItem(
            annotations=[Annotation(result=objs + relations)],
            predictions=[],
            data=Data(text=text),
        )
        self.labelstudio_data.__root__.append(item)

    def convert_annotation_from_bd(
        self, annotations: BadgerdocAnnotation, tokens: List[BadgerdocToken]
    ) -> List[ResultItem]:
        objs = annotations.pages[0].objs
        result_items = []
        for obj in objs:
            if not obj.tokens:
                continue
            item = ResultItem(
                id=obj.id,
                from_name="label",
                to_name="text",
                type="labels",
                origin="manual",
                value=Value(
                    start=min(obj.tokens),
                    end=max(obj.tokens) + 1,
                    text="".join(tokens[index].text for index in obj.tokens),
                    labels=[obj.category],
                ),
            )
            result_items.append(item)
        return result_items

    def convert_relation_from_bd(
        self, annotations: BadgerdocAnnotation, tokens: List[BadgerdocToken]
    ) -> List[ResultItem]:
        objs = annotations.pages[0].objs
        result_items = []
        for obj in objs:
            if not obj.links:
                continue
            for link in obj.links:
                item = ResultItem(
                    from_id=obj.id,
                    to_id=link.to,
                    type="relation",
                    direction=self.form_link_direction(link),
                    labels=[link.category_id]
                )
                result_items.append(item)
        return result_items

    def form_link_direction(self, link: AnnotationLink) -> str:
        # TODO: add logic
        return "right"

    def export_json(self, path: Path):
        path.write_text(self.labelstudio_data.json(indent=4))
