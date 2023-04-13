from typing import List

from convert.converters.base_format.models import annotation_practic
from convert.converters.base_format.models.annotation import (
    AnnotationLink,
    BadgerdocAnnotation,
    Obj,
    Page,
    Size,
)
from convert.converters.base_format.models.tokens import (
    Page as BadgerdocTokensPage,
)

FIRST_PAGE = 0


class AnnotationConverterPractic:
    def __init__(
        self,
        theoretic_annotation: BadgerdocAnnotation,
        theoretic_tokens: BadgerdocTokensPage,
    ):
        self.theoretic_annotation = theoretic_annotation
        self.theoretic_tokens = theoretic_tokens

    def convert(self) -> annotation_practic.BadgerdocAnnotation:
        page_theoretic = self.theoretic_annotation.pages[FIRST_PAGE]

        return annotation_practic.BadgerdocAnnotation(
            size=page_theoretic.size,
            page_num=page_theoretic.page_num,
            objs=self.convert_objs(page_theoretic.objs),
        )

    def convert_objs(
        self, objs_theoretic: List[Obj]
    ) -> List[annotation_practic.Obj]:
        objs = []
        for obj_theoretic in objs_theoretic:
            tokens = self.convert_tokens(obj_theoretic.tokens)
            links = self.convert_links(obj_theoretic.links)
            text = self.convert_text(obj_theoretic.tokens)
            obj = annotation_practic.Obj(
                id=obj_theoretic.id,
                type=obj_theoretic.type,
                bbox=obj_theoretic.bbox,
                category=obj_theoretic.category,
                text=text,
                data=annotation_practic.AnnotationTokens(
                    tokens=tokens,
                    dataAttributes=obj_theoretic.data.get(
                        "dataAttributes", []
                    ),
                ),
                links=links,
            )
            objs.append(obj)
        return objs

    def convert_tokens(
        self, theoretic_token_ids: List[int]
    ) -> List[annotation_practic.AnnotationToken]:
        tokens = []
        for token_id_theoretic in theoretic_token_ids:
            token_theoretic = self.theoretic_tokens.objs[token_id_theoretic]
            token = annotation_practic.AnnotationToken(
                id=token_id_theoretic,
                text=f"{token_theoretic.previous or ''}{token_theoretic.text}{token_theoretic.after or ''}",
                x=token_theoretic.bbox[0],
                y=token_theoretic.bbox[1],
                width=(token_theoretic.bbox[2] - token_theoretic.bbox[0]),
                height=(token_theoretic.bbox[3] - token_theoretic.bbox[1]),
            )
            tokens.append(token)
        return tokens

    @staticmethod
    def convert_links(
        theoretic_links: List[annotation_practic.AnnotationLink],
    ) -> List[annotation_practic.AnnotationLink]:
        links = []
        for link_theoretic in theoretic_links:
            link = annotation_practic.AnnotationLink(**link_theoretic.dict())
            links.append(link)
        return links

    def convert_text(self, token_ids: List[int]) -> str:
        text = ""
        for token_id in token_ids:
            token = self.theoretic_tokens.objs[token_id]
            full_token_text = (
                f"{token.previous or ''}{token.text}{token.after or ''}"
            )
            text = text + full_token_text
        return text.strip()


class AnnotationConverterToTheory:
    def __init__(
        self,
        practic_annotations: annotation_practic.BadgerdocAnnotation,
    ):
        self.practic_annotations = practic_annotations

    def convert(self) -> BadgerdocAnnotation:
        page_practic = self.practic_annotations

        objs = self.convert_objs(page_practic.objs)
        page = Page(
            size=Size(**page_practic.size.dict()),
            page_num=page_practic.page_num,
            objs=objs,
        )

        annotation = BadgerdocAnnotation(
            revision="", pages=[page], validated=[], failed_validation_pages=[]
        )
        return annotation

    def convert_objs(
        self, objs_practic: List[annotation_practic.Obj]
    ) -> List[Obj]:
        objs = []
        for obj_practic in objs_practic:
            token_ids = self.convert_tokens(obj_practic.data.tokens)
            links = self.convert_links(obj_practic.links)
            obj = Obj(
                id=obj_practic.id,
                type=obj_practic.type,
                bbox=obj_practic.bbox,
                category=obj_practic.category,
                data=obj_practic.data,
                tokens=token_ids,
                links=links,
            )
            objs.append(obj)
        return objs

    @staticmethod
    def convert_tokens(
        practic_tokens: List[annotation_practic.AnnotationToken],
    ) -> List[int]:
        return [practic_token.id for practic_token in practic_tokens]

    @staticmethod
    def convert_links(
        practic_links: List[annotation_practic.AnnotationLink],
    ) -> List[AnnotationLink]:
        return [
            AnnotationLink.parse_obj(practic_link.dict())
            for practic_link in practic_links
        ]
