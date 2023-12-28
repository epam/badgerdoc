from typing import Any, Dict


def map_request_to_filter(
    fields: Dict[str, Any], model: str
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "pagination": {},
        "filters": [],
        "sorting": [],
    }

    pagination = fields.get("pagination")
    if pagination:
        result["pagination"].update(pagination)

    filters = fields.get("filters")
    if filters:
        for filter_ in filters:
            field = filter_.get("field")
            op = filter_.get("operator")
            value = filter_.get("value")
            filter_row = {
                "model": model,
                "field": field,
                "op": op,
                "value": value,
            }
            result["filters"].append(filter_row)

    sorting = fields.get("sorting")
    if sorting:
        for sort_ in sorting:
            field = sort_.get("field")
            direction = sort_.get("direction")
            sort_row = {
                "model": model,
                "field": field,
                "direction": direction,
            }
            result["sorting"].append(sort_row)

    return result
