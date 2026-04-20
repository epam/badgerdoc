from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models import QuerySet


class TaskStatus(models.Model):
    name = models.CharField(max_length=50)
    parent = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="children"
    )
    order = models.PositiveIntegerField()

    if TYPE_CHECKING:
        children: "QuerySet[TaskStatus]"

    class Meta:
        db_table = "task_status"
        ordering = ["order"]
        verbose_name_plural = "Task statuses"

    def __str__(self):
        return self.name
