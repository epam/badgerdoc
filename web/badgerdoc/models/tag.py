from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models import QuerySet


class Tag(models.Model):
    tag = models.CharField(max_length=50, unique=True)
    literal = models.CharField(max_length=50, blank=True, default="")
    order = models.PositiveIntegerField()

    if TYPE_CHECKING:
        children: "QuerySet[Tag]"

    class Meta:
        db_table = "tag"
        ordering = ["order"]
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.tag
