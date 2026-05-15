from django.apps import apps
from django.db import models


def build_document_path(document_id: int) -> str:
    # NOTE: executes one query per level — may be slow for deep document hierarchies.
    document_model = apps.get_model("badgerdoc", "Document")
    parts: list[str] = []
    current_id: int | None = document_id
    while current_id is not None:
        node_id, parent_id = document_model.objects.values_list(
            "id", "parent_document_id"
        ).get(pk=current_id)
        parts.append(str(node_id))
        current_id = parent_id
    parts.reverse()
    return "/".join(parts) + "/"


class AgentLog(models.Model):

    class Level(models.TextChoices):
        DEBUG = ("DEBUG", "Debug")
        INFO = ("INFO", "Info")
        WARNING = ("WARNING", "Warning")
        ERROR = ("ERROR", "Error")
        CRITICAL = ("CRITICAL", "Critical")

    class Source(models.TextChoices):
        TEMPORAL = ("Temporal", "Temporal")
        DJANGO = ("Django", "Django")

    document = models.ForeignKey(
        "Document",
        on_delete=models.CASCADE,
        related_name="agent_logs",
    )
    task = models.ForeignKey(
        "Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_logs",
    )
    level = models.CharField(
        max_length=8,
        choices=Level.choices,
        default=Level.INFO,
    )
    source = models.CharField(
        max_length=16,
        choices=Source.choices,
    )
    log = models.JSONField()
    path = models.CharField(
        max_length=1024,
        default="",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "badgerdoc_agent_log"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["document", "created_at"]),
            models.Index(fields=["document", "task", "created_at"]),
        ]
        permissions = [
            ("can_write_log", "Can write agent log"),
        ]

    def save(self, *args, **kwargs) -> None:
        if not self.path:
            self.path = build_document_path(self.document_id)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        task_part = f" / task {self.task_id}" if self.task_id else ""
        return f"[{self.level}] doc {self.document_id}{task_part} @ {self.created_at}"
