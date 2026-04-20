from django.core.exceptions import ValidationError


def validate_tag_list(value: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        raise ValidationError("Tag must be a list")
    for item in value:
        if not isinstance(item, str):
            raise ValidationError("All tags must be strings")


def validate_extraction_scope_list(value: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        raise ValidationError("Extraction scope must be a list")

    valid_scopes = ["document", "page", "extraction"]
    valid_scope_labels = ["Document", "Page", "Extraction"]
    for item in value:
        if not isinstance(item, str):
            raise ValidationError("All extraction scopes must be strings")
        if item not in valid_scopes:
            raise ValidationError(
                f"Invalid extraction scope '{item}'. Valid options: {', '.join(valid_scope_labels)}"
            )
