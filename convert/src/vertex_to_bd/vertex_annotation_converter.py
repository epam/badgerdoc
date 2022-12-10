from typing import Dict, List

from .models import (
    BadgerdocAnnotationToken,
    BadgerdocToken,
    VertexAnnotationToken,
)


class VertexToBadgerdocAnnotationConverter:
    # FIXME: when requirements will be set
    def __init__(self, page_border_offset):
        self.page_border_offset = page_border_offset

    def convert(
        self,
        badgerdoc_tokens: List[BadgerdocToken],
        vertext_annotation_raw: List[Dict],
    ):
        vertext_annotation = [
            VertexAnnotationToken.parse_obj(i) for i in vertext_annotation_raw
        ]
        bd_annotation = []
        for vertex_token in vertext_annotation:
            tokens = badgerdoc_tokens[vertex_token.begin : vertex_token.end]
            bbox = [
                min([t.bbox[0] for t in tokens]),
                min([t.bbox[1] for t in tokens]),
                max([t.bbox[2] for t in tokens]),
                max([t.bbox[3] for t in tokens]),
            ]
            bd_token = BadgerdocAnnotationToken(
                id=int(vertex_token.id_),
                links=[int(i) for i in vertex_token.links],
                category=vertex_token.entity_type,
                data={"entity": {"id": vertex_token.entity_name}},
                tokens=list(range(vertex_token.begin, vertex_token.end)),
                bbox=bbox,
            )
            bd_annotation.append(bd_token)

        page_width = (
            max([t.bbox[2] for t in badgerdoc_tokens])
            + self.page_border_offset
        )
        page_height = (
            max([t.bbox[2] for t in badgerdoc_tokens])
            + self.page_border_offset
        )
        return {
            "revision": "revision-1",
            "pages": [
                {
                    "size": {"width": page_width, "height": page_height},
                    "page_num": 1,
                    "objs": [i.dict(by_alias=True) for i in bd_annotation],
                    "validated": [],
                    "failed_validation_pages": [],
                }
            ],
        }
