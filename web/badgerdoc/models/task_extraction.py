from django.db import models


class TaskExtraction(models.Model):
    task = models.ForeignKey(
        "Task",
        on_delete=models.CASCADE,
        related_name="task_extractions",
        help_text="Link task to extraction in case if task type: Extraction",
    )
    extraction = models.ForeignKey(
        "Extraction",
        on_delete=models.CASCADE,
        related_name="task_assignments",
        help_text="Link extraction to task in case if task type: Extraction",
    )

    class Meta:
        db_table = "user_task_extraction"
        constraints = [
            models.UniqueConstraint(
                fields=["task", "extraction"], name="unique_task_extraction"
            )
        ]

    def __str__(self):
        return f"Task {self.task.id} - Extraction {self.extraction.id}"
