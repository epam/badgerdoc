from typing import List

from ..models import bd_annotation_model_practic
from ..models.bd_annotation_model import AnnotationLink, BadgerdocAnnotation, Obj, Page
from ..models.bd_tokens_model import Page as BadgerdocTokensPage

FIRST_PAGE = 0


class AnnotationConverterPractic:
    def __init__(
        self,
        theoretic_annotation: BadgerdocAnnotation,
        theoretic_tokens: BadgerdocTokensPage,
    ):
        self.theoretic_annotation = theoretic_annotation
        self.theoretic_tokens = theoretic_tokens

    def convert(self) -> bd_annotation_model_practic.BadgerdocAnnotation:
        page_theoretic = self.theoretic_annotation.pages[FIRST_PAGE]
        page = bd_annotation_model_practic.Page(
            size=page_theoretic.size,
            page_num=page_theoretic.page_num,
            objs=self.convert_objs(page_theoretic.objs),
        )

        annotation = bd_annotation_model_practic.BadgerdocAnnotation(
            pages=[page],
            revision=self.theoretic_annotation.revision,
            validated=self.theoretic_annotation.validated,
            failed_validation_pages=self.theoretic_annotation.failed_validation_pages,
        )
        return annotation

    def convert_objs(
        self, objs_theoretic: List[Obj]
    ) -> List[bd_annotation_model_practic.Obj]:
        objs = []
        for obj_theoretic in objs_theoretic:
            tokens = self.convert_tokens(obj_theoretic.tokens)
            links = self.convert_links(obj_theoretic.links)
            text = self.convert_text(obj_theoretic.tokens)

            obj = bd_annotation_model_practic.Obj(
                id=obj_theoretic.id,
                type=obj_theoretic.type,
                bbox=obj_theoretic.bbox,
                category=obj_theoretic.category,
                text=text,
                data=bd_annotation_model_practic.AnnotationTokens(
                    tokens=tokens
                ),
                links=links,
            )
            objs.append(obj)
        return objs

    def convert_tokens(
        self, theoretic_token_ids: List[int]
    ) -> List[bd_annotation_model_practic.AnnotationToken]:
        tokens = []
        for token_id_theoretic in theoretic_token_ids:
            token_theoretic = self.theoretic_tokens.objs[token_id_theoretic]
            token = bd_annotation_model_practic.AnnotationToken(
                id=token_id_theoretic,
                text=token_theoretic.text,
                x=token_theoretic.bbox[0],
                y=token_theoretic.bbox[1],
                width=(token_theoretic.bbox[2] - token_theoretic.bbox[0]),
                height=(token_theoretic.bbox[3] - token_theoretic.bbox[1]),
            )
            tokens.append(token)
        return tokens

    def convert_links(
        self, theoretic_links: List[bd_annotation_model_practic.AnnotationLink]
    ) -> List[bd_annotation_model_practic.AnnotationLink]:
        links = []
        for link_theoretic in theoretic_links:
            link = bd_annotation_model_practic.AnnotationLink(
                category_id="Link",
                to=link_theoretic.to,
                type="directional",
                page_num=1,
            )
            links.append(link)
        return links

    def convert_text(self, theoretic_tokens: List[int]) -> str:
        text = "".join(
            self.theoretic_tokens.objs[token_id_theoretic].text
            for token_id_theoretic in theoretic_tokens
        )
        return text


class AnnotationConverterToTheory:
    def __init__(
        self,
        practic_annotations: bd_annotation_model_practic.BadgerdocAnnotation,
    ):
        self.practic_annotations = practic_annotations

    def convert(self) -> BadgerdocAnnotation:
        page_practic = self.practic_annotations.pages[FIRST_PAGE]

        objs = self.convert_objs(page_practic.objs)
        page = Page(
            size=page_practic.size, page_num=page_practic.page_num, objs=objs
        )

        annotation = BadgerdocAnnotation(
            revision=self.practic_annotations.revision,
            pages=[page],
            validated=self.practic_annotations.validated,
            failed_validation_pages=self.practic_annotations.failed_validation_pages,
        )
        return annotation

    def convert_objs(
        self, objs_practic: List[bd_annotation_model_practic.Obj]
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
                data=None,
                tokens=token_ids,
                links=links,
            )
            objs.append(obj)
        return objs

    def convert_tokens(
        self, practic_tokens: List[bd_annotation_model_practic.AnnotationToken]
    ) -> List[int]:
        return [practic_token.id for practic_token in practic_tokens]

    def convert_links(
        self, practic_links: List[bd_annotation_model_practic.AnnotationLink]
    ) -> List[AnnotationLink]:
        return [AnnotationLink.parse_obj(practic_link.dict()) for practic_link in practic_links]
