from typing import Any
from urllib.parse import urlencode

from django.core.paginator import Paginator
from rest_framework import serializers
from rest_framework.request import Request


def badgerdoc_form_pagination(request: Request, queryset: Any) -> Any:
    page = request.GET.get("page", 1)
    try:
        page_size = int(request.GET.get("page_size", 20))
    except (ValueError, TypeError):
        page_size = 20
    page_size = min(page_size, 100)

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    return page_obj


def badgerdoc_paginate(
    request: Request, page_obj: Any
) -> tuple[str | None, str | None]:
    next_url = None
    previous_url = None

    params = request.GET.copy()

    if page_obj.has_next():
        params["page"] = page_obj.next_page_number()
        next_url = f"?{urlencode(params)}"

    if page_obj.has_previous():
        params["page"] = page_obj.previous_page_number()
        previous_url = f"?{urlencode(params)}"

    return next_url, previous_url


def build_paginated_serializer(
    item_serializer: type[serializers.ModelSerializer],
):
    base_name = (
        getattr(item_serializer, "__name__", None)
        or item_serializer.__class__.__name__
    )
    meta = getattr(item_serializer, "Meta", None)
    ref_base = getattr(meta, "ref_name", None) or base_name

    paginated_ref = f"Paginated{ref_base}"

    class PaginatedSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        next = serializers.CharField(allow_null=True, required=False)
        previous = serializers.CharField(allow_null=True, required=False)
        results = item_serializer(many=True)

        class Meta:
            ref_name = paginated_ref

    return PaginatedSerializer
