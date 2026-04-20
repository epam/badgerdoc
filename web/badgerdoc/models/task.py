from django.contrib.auth.models import User
from django.db import models

from badgerdoc.models import _validation, base


class Task(base.TimestampedModel):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    document = models.ForeignKey(
        "Document",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    status = models.ForeignKey(
        "TaskStatus",
        on_delete=models.PROTECT,
        related_name="tasks",
    )
    tags = models.JSONField(
        blank=True,
        null=True,
        validators=[_validation.validate_tag_list],
        help_text="List of tags as strings",
    )

    class Meta:
        db_table = "user_tasks"
        ordering = ["-id"]
        permissions = [
            (
                "view_other_users_tasks",
                "Can view other users tasks",
            ),
        ]

    def __str__(self):
        return f"Task {self.id} - {self.status.name} - {self.user.username}"
