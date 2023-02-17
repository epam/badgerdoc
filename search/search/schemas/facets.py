from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import aiocache.serializers
import search.common_utils as utils
from pydantic import BaseModel, Field
from search.config import settings
from search.es import INDEX_SETTINGS, fetch

__excluded_agg_types = ("text",)


def facet_condition(properties: Dict[str, Any]) -> List[str]:
    return [
        el
        for el in properties
        if properties[el].get("type") not in __excluded_agg_types
    ]


fields = utils.get_mapping_fields(INDEX_SETTINGS)
FACET_FIELDS = facet_condition(fields)
FACET_ENUM = utils.enum_generator(FACET_FIELDS, "FACET_FIELDS")


class FacetOperator(str, Enum):
    IN = "in"
    NOT_IN = "not_in"


class FilterParams(BaseModel):
    field: FACET_ENUM = Field(
        description="*Available fields for facets*", example="category"
    )
    operator: FacetOperator = Field(
        description="*Available filter operators*", example="in"
    )
    value: List[Union[int, float, str]] = Field(
        description="*An array of str|float|int values*",
        example=["Header", "Title"],
    )

    @property
    def filter_template(self) -> Dict[str, Any]:
        return {"terms": {self.field: self.value}}

    def apply_filter(self, query: Dict[str, Any]) -> Dict[str, Any]:
        facets = query["aggs"]
        for facet_name, facet_body in facets.items():
            if facet_name == self.field:
                continue

            if self.operator == FacetOperator.IN:
                facet_body["filter"]["bool"]["must"].append(self.filter_template)
            if self.operator == FacetOperator.NOT_IN:
                facet_body["filter"]["bool"]["must_not"].append(self.filter_template)

        return query


class FacetParams(BaseModel):
    name: FACET_ENUM = Field(
        description="*Available fields for facets*", example="category"
    )
    limit: int = Field(
        10,
        ge=1,
        description="*A limit that will be returned for particular field*",
        example=10,
        le=100,
    )

    @property
    def facet_template(self) -> Dict[str, Any]:
        template = {
            self.name: {
                "filter": {"bool": {"must": [], "must_not": []}},
                "aggs": {
                    self.name: {"terms": {"field": self.name, "size": self.limit}}
                },
            }
        }
        return template


class FacetsRequest(BaseModel):
    query: Optional[str] = Field(
        description="*Match query in a text type field*",
        example="Elasticsearch",
    )
    facets: List[FacetParams] = Field(description="*An array for ES aggregations*")
    filters: Optional[List[FilterParams]] = Field(description="*Filters for facets*")

    def _build_facets(self, query: Dict[str, Any]) -> Dict[str, Any]:
        for facet in self.facets:
            query["aggs"].update(facet.facet_template)
        return query

    def _build_match_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        q = {
            "query": {
                "match": {
                    "content": {
                        "query": self.query,
                        "minimum_should_match": "81%",
                    }
                }
            }
        }
        query.update(q)
        return query

    def _build_filters(self, query: Dict[str, Any]) -> Dict[str, Any]:
        for fil in self.filters:
            fil.apply_filter(query)
        return query

    def build_es_query(self) -> Dict[str, Any]:
        _q = {"aggs": {}, "size": 0}
        self._build_facets(_q)
        if self.query:
            self._build_match_query(_q)
        if self.filters:
            self._build_filters(_q)
        return _q


class AggResult(BaseModel):
    id: Union[int, str] = Field(description="*Aggregation key id*", example="Header")
    count: int = Field(description="*Count of aggregated docs*", example=10)
    name: Optional[str] = Field(description="*A name of a category or a job*")

    @staticmethod
    def parse_es_agg_doc(es_doc: Dict[str, Any]) -> "AggResult":
        return AggResult(id=es_doc.get("key", ""), count=es_doc.get("doc_count", 0))


class FacetBodyResponse(BaseModel):
    name: str = Field(description="*A name of aggregation*", example="category")
    values: List[AggResult] = Field(description="*An array aggregation results*")

    async def adjust_facet(self, tenant: str, token: str) -> None:
        if self.name not in settings.computed_fields:
            return

        ids: Union[Tuple[str, ...], Tuple[int, ...]] = tuple(
            agg.id for agg in self.values
        )
        url: str = ""
        if self.name == "category":
            ids = tuple(map(str, ids))
            url = settings.annotation_categories_search_url
        if self.name == "job_id":
            url = settings.jobs_search_url

        resp = await self.fetch_data(tenant, token, url, ids)
        self.update_data(resp)
        return

    def update_data(self, resp: Dict[str, Any]) -> None:
        data = resp.get("data", [])
        for el in data:
            for agg in self.values:
                if str(agg.id) == str(el.get("id")):
                    agg.name = el.get("name")
        return

    @aiocache.cached(ttl=300, serializer=aiocache.serializers.JsonSerializer())
    async def fetch_data(
        self,
        tenant: str,
        token: str,
        url: str,
        ids: Union[Tuple[str, ...], Tuple[int, ...]],
    ) -> Dict[str, Any]:
        headers = {
            "X-Current-Tenant": tenant,
            "Authorization": f"Bearer {token}",
        }
        body = {
            "pagination": {"page_num": 1, "page_size": 100},
            "filters": [{"field": "id", "operator": "in", "value": ids}],
        }
        _, q = await fetch("POST", url, body=body, headers=headers)
        return q


class FacetsResponse(BaseModel):
    facets: List[FacetBodyResponse] = Field(
        example=[
            {
                "name": "category",
                "values": [
                    {"id": "Header", "count": 20},
                    {"id": "Title", "count": 5},
                    {"id": "Table", "count": 1},
                ],
            },
            {
                "name": "job_id",
                "values": [{"id": 409, "count": 10}, {"id": 42, "count": 20}],
            },
        ]
    )

    @staticmethod
    def parse_es_response(es_resp: Dict[str, Any]) -> "FacetsResponse":
        facets = []
        agg = es_resp.get("aggregations", {})
        for name in agg:
            docs = agg[name][name].get("buckets", [])
            array_docs = list(map(AggResult.parse_es_agg_doc, docs))
            facets.append(FacetBodyResponse(name=name, values=array_docs))
        return FacetsResponse(facets=facets)

    async def adjust_facet_result(self, tenant: str, token: str) -> None:
        for facet in self.facets:
            await facet.adjust_facet(tenant, token)
        return
