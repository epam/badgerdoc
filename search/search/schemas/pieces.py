import asyncio
import enum
import re
import math
from collections import namedtuple
from functools import reduce
from typing import Any, Dict, List, Optional, Union

import pydantic
import search.embeddings as embeddings
import search.querydsl as query_dsl
import search.common_utils as utils
import search.es as es
from search.logger import logger

__excluded_types = ("text",)
PaginationParams = namedtuple(
    "PaginationParams",
    ["page_num", "page_size", "pages", "total"],
)


def pieces_condition(properties: Dict[str, Any]) -> List[str]:
    return [
        el for el in properties if properties[el].get("type") not in __excluded_types
    ]


fields = pieces_condition(utils.get_mapping_fields(es.INDEX_SETTINGS))
PIECES_ENUM = utils.enum_generator(fields, "PIECES_ENUM")


class GeomObject(pydantic.BaseModel):
    category: str = pydantic.Field(..., example="Header")
    content: str = pydantic.Field(..., example="ElasticSearch")
    document_id: pydantic.conint(ge=1) = pydantic.Field(..., example=1)  # type: ignore
    page_number: pydantic.conint(ge=1) = pydantic.Field(..., example=1)  # type: ignore
    highlight_name: Optional[str] = pydantic.Field(None)
    is_annotation: Optional[bool] = pydantic.Field(False)
    is_highlight: Optional[bool] = pydantic.Field(False)
    sentence_num: Optional[int] = pydantic.Field(None)
    bbox: Optional[pydantic.conlist(float, min_items=4, max_items=4)] = pydantic.Field(
        None, example=[1.5, 1.5, 1.5, 1.5]
    )  # type: ignore
    tokens: Optional[List[str]] = pydantic.Field(
        None, example=["token1", "token2", "token3"]
    )
    job_id: pydantic.conint(ge=1) = pydantic.Field(..., example=1)  # type: ignore


class SearchResultSchema(pydantic.BaseModel):
    current_page: pydantic.conint(ge=1)
    page_size: pydantic.conint(ge=1)
    short_answer: str = pydantic.Field(..., example="short answer")
    total_objects: pydantic.conint(ge=0)
    text_pieces: List[GeomObject]


class PieceOperators(str, enum.Enum):
    EQ = "eq"
    IN = "in"
    NOT_IN = "not_in"


class PieceSortDirections(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class PiecePagination(pydantic.BaseModel):
    page_num: int = pydantic.Field(1, gt=0)
    page_size: int = pydantic.Field(50, gt=0)

    def build_pagination_body(self) -> Dict[str, Any]:
        return {
            "from": (self.page_num - 1) * self.page_size,
            "size": self.page_size,
        }


class PieceFilter(pydantic.BaseModel):
    field: PIECES_ENUM
    operator: PieceOperators
    value: Union[int, float, str, List[Union[int, float, str]]]

    def get_filter_template(self) -> Dict[str, Any]:
        if not isinstance(self.value, list):
            self.value = [self.value]
        return {"terms": {self.field.value: self.value}}

    @property
    def is_include(self) -> bool:
        return self.operator in (PieceOperators.IN, PieceOperators.EQ)

    async def adjust_for_child_categories(self, tenant: str, token: str) -> List[str]:
        if not isinstance(self.value, list):
            self.value = [self.value]
        tasks = []
        for category in self.value:
            task = asyncio.create_task(es.add_child_categories(category, tenant, token))
            tasks.append(task)
        res = await asyncio.gather(*tasks)
        new_categories = list(reduce(lambda a, b: a & b, map(set, res)))
        self.value.extend(new_categories)
        return new_categories


class PieceSort(pydantic.BaseModel):
    field: PIECES_ENUM
    direction: PieceSortDirections

    def build_sorting_body(self) -> Dict[str, Any]:
        return {self.field: {"order": self.direction}}


class PiecesRequest(pydantic.BaseModel):
    query: Optional[str]
    method: Optional[str]
    scope: Optional[str]
    pagination: Optional[PiecePagination]
    filters: Optional[List[PieceFilter]]
    sorting: Optional[List[PieceSort]]

    @pydantic.root_validator(pre=True)
    def check_pagination(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if not value.get("pagination"):
            value["pagination"] = PiecePagination(page_num=1, page_size=50)
        return value

    def _build_sorts(self) -> List[Dict[str, Any]]:
        sorts = []
        for sort in self.sorting:
            sorts.append(sort.build_sorting_body())
        return sorts

    def _apply_filters(self, query: Dict[str, Any]) -> Dict[str, Any]:
        for filter_ in self.filters:
            if filter_.is_include:
                query["query"]["bool"]["must"].append(filter_.get_filter_template())
            if not filter_.is_include:
                query["query"]["bool"]["must_not"].append(filter_.get_filter_template())
        return query

    def _apply_sort(self, query: Dict[str, Any]) -> Dict[str, Any]:
        query["sort"] = self._build_sorts()
        return query

    def _apply_es_pagination(self, query: Dict[str, Any]) -> Dict[str, Any]:
        query.update(self.pagination.build_pagination_body())
        return query

    def _apply_embed_txt_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("sim search")
        query["query"]["bool"]["must"].append(query_dsl.get_subquery_embed_txt(self.query))
        return query

    def _apply_qa_embeddings(self, query: Dict[str, Any]) -> Dict[str, Any]:
        query["query"]["bool"]["must"].append(query_dsl.get_subquery_embed_qa_txt(self.query))
        return query

    def _apply_text_match_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        query["query"]["bool"]["must"].append(query_dsl.get_subquery_text_match(self.query))
        return query

    @property
    def _is_match_all(self) -> bool:
        if self.query is None and self.filters is None:
            return True
        return False

    @staticmethod
    def _match_all(query: Dict[str, Any]) -> Dict[str, Any]:
        query["query"] = {"match_all": {}}
        return query

    def build_query(self):
        _q = {"query": {},
              "_source": ["category", "page_number", "bbox", "content", "document_id", "job_id", "tokens"]}
        self._apply_es_pagination(_q)
        if self.sorting:
            self._apply_sort(_q)
        if self._is_match_all:
            return self._match_all(_q)
        _q["query"]["bool"] = {"must": [], "must_not": []}

        if self.filters:
            _q = self._apply_filters(_q)

        if self.method == "text":
            self._apply_text_match_query(_q)
        if self.method == "semantic":
            logger.info(f"sim search {self.query}")
            self._apply_embed_txt_query(_q)
        if self.method == "qa":
            self._apply_qa_embeddings(_q)
        _q["query"]["bool"]["must"].append(query_dsl.get_filter_by_scope(self.scope))
        #logger.info(_q)
        return _q

    async def adjust_categories(self, tenant: str, token: str) -> None:
        if not self.filters:
            return
        for filter_ in self.filters:
            if filter_.field == "category":
                await filter_.adjust_for_child_categories(tenant, token)
        return


class CombinedPiecesRequest(pydantic.BaseModel):
    combined_query: Optional[List[PiecesRequest]]


class PaginationOut(PiecePagination):
    pages: int
    total: int


def get_idx(context):
    matches = re.findall(r"\b[0-9]\b", context)

    if matches and matches[0].isdigit():
        return int(matches[0])
    return 0


class SearchResultSchema2(pydantic.BaseModel):
    pagination: PaginationOut
    short_answer: Optional[str]
    data: List[GeomObject]

    @staticmethod
    def __make_pag_params(
            resp: Dict[str, Any], pag_in: PiecePagination
    ) -> PaginationParams:
        total_results = resp["hits"]["total"]["value"]
        pages = SearchResultSchema2.__calculate_num_pages(
            pag_in.page_size, total_results
        )
        return PaginationParams(pag_in.page_num, pag_in.page_size, pages, total_results)

    @staticmethod
    def __calculate_num_pages(page_size: int, total_results: int) -> int:
        return math.ceil(float(total_results) / float(page_size))


    async def adjust_by_generative_answers(self, query: str):
        """
       Collect text pieces from ES and append generative answer from LLM.
       """
        contexts = [x.content for x in self.data]
        opinions = await embeddings.get_gpt_opinion(contexts, query)
        if "answer" in opinions:
            highlight_cards = opinions["context_number"]
            if not isinstance(highlight_cards, list):
                highlight_cards = [highlight_cards]
            opinions_mapped = {}
            if len(highlight_cards) == 1:
                opinions_mapped[highlight_cards[0]] = opinions["answer"]
            if len(highlight_cards) > 1 and "context" in opinions["answer"]:
                pattern = r'(.*?)\((.*?)\)\s?'
                matches = re.findall(pattern, opinions["answer"])
                opinions_mapped = {get_idx(context): text for text, context in matches}

                logger.info(f"extracted from generative response {opinions_mapped}")
            logger.info(highlight_cards)
            # map to original items
            for i, item in enumerate(self.data):
                if (i + 1) in highlight_cards:
                    item.highlight_name = opinions_mapped[i + 1]
                    item.is_highlight = True
            self.short_answer = opinions["answer"]
        return

    @staticmethod
    def parse_es_response(
            es_response: Dict[str, Any], pag_in: PiecePagination
    ) -> "SearchResultSchema2":
        pag_params = SearchResultSchema2.__make_pag_params(es_response, pag_in)
        pag = PaginationOut(
            page_num=pag_params.page_num,
            page_size=pag_params.page_size,
            pages=pag_params.pages,
            total=pag_params.total,
        )
        hits = (x["_source"] for x in es_response["hits"]["hits"])
        items = pydantic.parse_obj_as(List[GeomObject], hits)

        return SearchResultSchema2(pagination=pag, data=items)


class CombinedPiecesRequest(pydantic.BaseModel):
    all_results: Optional[List[SearchResultSchema2]]

    """
   Takes first top 5 items from each & combines output. 
   """

    async def adjust_by_generative_answers(self, query: str):
        contexts = [x.content for x in self.all_results[0]]
