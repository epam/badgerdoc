from typing import Any, List, Optional, Tuple

from src.badgerdoc.bd_annotation_model import (
    AnnotationLink,
    BadgerdocAnnotation,
    Obj,
    Page,
    Size,
)
from src.badgerdoc.bd_tokens_model import Page as BadgerdocTokensPage
from src.labelstudio.ls_models import (
    Annotation,
    LabelStudioModel,
    ResultItem,
)

from .annotation_converter_practic import AnnotationConverterPractic


def safe_list_get(any_list: List, idx: int, default: Any = None) -> Any:
    if any_list:
        try:
            return any_list[idx]
        except IndexError:
            return default
    return default


class AnnotationConverter:
    LABELS = "labels"
    RELATION = "relation"

    def convert(
        self,
        annotations: LabelStudioModel,
        badgerdoc_tokens: BadgerdocTokensPage,
    ):
        model_items = annotations.__root__
        badgerdoc_annotations = BadgerdocAnnotation(
            pages=[
                Page(
                    page_num=1,
                    size=Size(
                        width=badgerdoc_tokens.size.width,
                        height=badgerdoc_tokens.size.height,
                    ),
                )
            ]
        )
        for model_item in model_items:
            for annotation in model_item.annotations:
                self.process_annotation(
                    annotation, badgerdoc_annotations, badgerdoc_tokens
                )

        badgerdoc_annotations_practic = AnnotationConverterPractic(
            badgerdoc_annotations, badgerdoc_tokens
        ).convert()
        return badgerdoc_annotations_practic

    def _is_labels(self, labelstudio_item: ResultItem) -> bool:
        return labelstudio_item.type == self.LABELS

    def _is_relation(self, labelstudio_item: ResultItem) -> bool:
        return labelstudio_item.type == self.RELATION

    def process_annotation(
        self,
        annotation: Annotation,
        badgerdoc_annotations: BadgerdocAnnotation,
        badgerdoc_tokens: BadgerdocTokensPage,
    ) -> None:
        for labelstudio_item in annotation.result:
            self.process_labels(
                badgerdoc_annotations,
                labelstudio_item,
                badgerdoc_tokens,
            )
        for labelstudio_item in annotation.result:
            self.process_relations(badgerdoc_annotations, labelstudio_item)

    def process_labels(
        self,
        badgerdoc_annotations: BadgerdocAnnotation,
        labelstudio_item: ResultItem,
        badgerdoc_tokens: BadgerdocTokensPage,
    ) -> None:
        if not self._is_labels(labelstudio_item):
            return

        value = labelstudio_item.value
        start_id = len(badgerdoc_annotations.pages[0].objs)
        for id_, label in enumerate(value.labels, start=start_id):
            _inner_index_of_iteration = start_id - id_

            type_ = "text"
            tokens, bbox = self.get_token_indexes_and_form_bbox(
                value.start, value.end, badgerdoc_tokens
            )
            category = label
            data = {"source_id": labelstudio_item.id}

            taxon = safe_list_get(value.taxons, _inner_index_of_iteration)
            if taxon:
                data["dataAttributes"] = [
                    {"name": "taxonomy", "type": "taxonomy", "value": taxon}
                ]

            bd_annotation = Obj(
                id=id_,
                type=type_,
                bbox=bbox,
                tokens=tokens,
                category=category,
                data=data,
            )
            badgerdoc_annotations.pages[0].objs.append(bd_annotation)

    def process_relations(
        self,
        badgerdoc_annotations: BadgerdocAnnotation,
        labelstudio_item: ResultItem,
    ):
        if not self._is_relation(labelstudio_item):
            return
        if not labelstudio_item.from_id or not labelstudio_item.to_id:
            raise KeyError("Bad relation id in a labelstudio file")
        source_obj = self.find_badgerdoc_annotation(
            badgerdoc_annotations, labelstudio_item.from_id
        )
        target_obj = self.find_badgerdoc_annotation(
            badgerdoc_annotations, labelstudio_item.to_id
        )
        if not source_obj or not target_obj:
            raise KeyError(
                "Can't find tokens during creation links for badgerdoc annotations"
            )

        link_label = "Link"
        if labelstudio_item.labels:
            if len(labelstudio_item.labels) > 0:
                link_label = labelstudio_item.labels[0]

        link = AnnotationLink(
            category_id=link_label,
            to=target_obj.id,
            type="directional",
            page_num=1,
        )
        source_obj.links.append(link)

    def get_token_indexes_and_form_bbox(
        self,
        offset_begin: int,
        offset_end: int,
        badgerdoc_tokens: BadgerdocTokensPage,
    ) -> Tuple[List[int], List[float]]:
        badgerdoc_annotation_token_indexes = list(
            range(offset_begin, offset_end)
        )
        bbox = self.form_common_bbox(
            [
                badgerdoc_tokens.objs[t].bbox
                for t in badgerdoc_annotation_token_indexes
            ]
        )
        return badgerdoc_annotation_token_indexes, bbox

    @staticmethod
    def form_common_bbox(bboxes: List[List[float]]) -> List[float]:
        return [
            min([bbox[0] for bbox in bboxes]),
            min([bbox[1] for bbox in bboxes]),
            max([bbox[2] for bbox in bboxes]),
            max([bbox[3] for bbox in bboxes]),
        ]

    @staticmethod
    def find_badgerdoc_annotation(
        badgerdoc_annotations: BadgerdocAnnotation,
        source_id: str,
    ) -> Optional[Obj]:
        for obj in badgerdoc_annotations.pages[0].objs:
            if obj.data["source_id"] == source_id:
                return obj
