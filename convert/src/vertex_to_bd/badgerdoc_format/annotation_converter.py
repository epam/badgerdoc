from typing import List, Optional, Tuple

from ..models.bd_annotation_model import BadgerdocAnnotation, Obj, Page, Size
from ..models.bd_tokens_model import Page as BadgerdocTokensPage
from ..models.vertex_models import LabelStudioModel, ModelItem, ResultItem


class AnnotationConverter:
    LABELS = "labels"
    RELATION = "relation"

    def convert(
        self,
        annotations: LabelStudioModel,
        badgerdoc_tokens: BadgerdocTokensPage,
    ):
        model_items: List[ModelItem] = annotations.__root__
        badgerdoc_annotations = BadgerdocAnnotation(
            pages=[Page(page_num=1, size=Size(width=100, height=100))]
        )
        for model_item in model_items:
            for annotation in model_item.annotations:
                for labelstudio_item in annotation.result:
                    self.process_labels(
                        badgerdoc_annotations,
                        labelstudio_item,
                        badgerdoc_tokens,
                    )
                for labelstudio_item in annotation.result:
                    self.process_relations(
                        badgerdoc_annotations, labelstudio_item
                    )
        return badgerdoc_annotations

    def _is_labels(self, labelstudio_item: ResultItem) -> bool:
        return labelstudio_item.type == self.LABELS

    def _is_relation(self, labelstudio_item: ResultItem) -> bool:
        return labelstudio_item.type == self.RELATION

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
            type_ = "text"
            # TODO: check start, end
            data = {"source_id": labelstudio_item.id}
            tokens, bbox = self.get_token_indexes_and_form_bbox(
                value.start, value.end, badgerdoc_tokens
            )
            category = label
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

        source_obj = self.find_badgerdoc_annotation(
            badgerdoc_annotations, labelstudio_item.from_id
        )
        target_obj = self.find_badgerdoc_annotation(
            badgerdoc_annotations, labelstudio_item.to_id
        )
        source_obj.links.append(target_obj.id)

    def get_token_indexes_and_form_bbox(
        self,
        offset_begin: int,
        offset_end: int,
        badgerdoc_tokens: BadgerdocTokensPage,
    ) -> Tuple[List[int], List[float]]:
        badgerdoc_annotation_token_indexes = list(
            range(offset_begin, offset_end + 1)
        )
        bbox = self.form_common_bbox(
            [
                badgerdoc_tokens.objs[t].bbox
                for t in badgerdoc_annotation_token_indexes
            ]
        )
        return badgerdoc_annotation_token_indexes, bbox

    def form_common_bbox(self, bboxes: List[List[float]]) -> List[float]:
        return [
            min([bbox[0] for bbox in bboxes]),
            min([bbox[1] for bbox in bboxes]),
            max([bbox[2] for bbox in bboxes]),
            max([bbox[3] for bbox in bboxes]),
        ]

    def find_badgerdoc_annotation(
        self,
        badgerdoc_annotations: BadgerdocAnnotation,
        source_id: str,
    ) -> Optional[Obj]:
        for obj in badgerdoc_annotations.pages[0].objs:
            if obj.data["source_id"] == source_id:
                return obj
