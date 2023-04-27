import math
from collections import namedtuple
from typing import Optional, Sequence, Tuple, TypeVar

from sqlalchemy.orm import Query

from .schema_generator import Page, PaginationOut

T = TypeVar("T")
PaginationParams = namedtuple(
    "PaginationParams",
    [
        "page_num",
        "page_size",
        "min_pages_left",
        "total",
        "has_more",
        "page_offset",
    ],
)


def make_pagination(
    initial_query: Query,
    page_size: int,
    page_offset: int,
    max_count: int,
    page_num: Optional[int] = None,
) -> Tuple[Query, PaginationParams]:
    output_query = initial_query.offset(page_offset).limit(page_size)

    total_results_query = initial_query.limit(max_count)
    if not page_num:  # "page_offset" is used instead of "page_num"
        total_results_query = total_results_query.offset(page_offset)
    total_results_count = total_results_query.count()

    has_more = total_results_count == max_count
    if total_results_count == max_count:
        total_results_count -= 1

    min_pages_left: int = _calculate_num_pages(page_size, total_results_count)

    return output_query, PaginationParams(
        page_num,
        page_size,
        min_pages_left,
        total_results_count,
        has_more,
        page_offset,
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
        page_offset=pag_params.page_offset,
    )
    return Page(pagination=pag, data=items)
