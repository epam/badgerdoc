import math
from collections import namedtuple
from typing import Sequence, Tuple, TypeVar

from sqlalchemy.orm import Query

from .schema_generator import Page, PaginationOut

T = TypeVar("T")
PaginationParams = namedtuple(
    "PaginationParams",
    ["page_num", "page_size", "min_pages_left", "total", "has_more"],
)


def make_pagination(
    query: Query, page_number: int, page_size: int
) -> Tuple[Query, PaginationParams]:
    has_more: bool = False
    max_count = page_size * 10 + 1
    total_results: int = query.limit(max_count).count()
    if total_results == max_count:
        has_more = True
        total_results -= 1
    query = query.limit(page_size)
    query = query.offset((page_number - 1) * page_size)
    min_num_pages: int = _calculate_num_pages(page_size, total_results)
    return query, PaginationParams(
        page_number, page_size, min_num_pages, total_results, has_more
    )


def _calculate_num_pages(page_size: int, total_results: int) -> int:
    return math.ceil(float(total_results) / float(page_size))


def paginate(items: Sequence[T], pag_params: PaginationParams) -> Page[T]:
    pag = PaginationOut(
        page_num=pag_params.page_num,
        page_size=pag_params.page_size,
        min_pages_left=pag_params.min_pages_left,
        total=pag_params.total,
        has_more=pag_params.has_more,
    )
    return Page(pagination=pag, data=items)
