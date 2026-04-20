def can_view_other_users_extractions(user) -> bool:
    return user.is_staff or user.has_perm(
        "badgerdoc.view_other_users_extractions"
    )


def can_view_other_users_document(user) -> bool:
    return user.is_staff or user.has_perm(
        "badgerdoc.view_other_users_document"
    )


def can_view_other_users_tasks(user) -> bool:
    return user.is_staff or user.has_perm("badgerdoc.view_other_users_tasks")


def can_delete_document(user) -> bool:
    return user.is_staff or user.has_perm("badgerdoc.can_delete_document")
