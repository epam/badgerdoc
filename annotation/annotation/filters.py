from filter_lib import create_filter_model

from annotation.models import (AnnotatedDoc, Category, Job,
                               ManualAnnotationTask, User)

CategoryFilter = create_filter_model(
    Category,
    exclude=[
        "metadata_",
        "tenant",
        "data_attributes",
        *[f"parent_id.{col}" for col in Category.__table__.columns.keys()],
        *[f"jobs.{col}" for col in Job.__table__.columns.keys()],
    ],
)

TaskFilter = create_filter_model(
    ManualAnnotationTask,
    exclude=[
        "pages",
        *[f"jobs.{col}" for col in Job.__table__.columns.keys()],
        *[f"user.{col}" for col in User.__table__.columns.keys()],
        *[f"docs.{col}" for col in AnnotatedDoc.__table__.columns.keys()],
    ],
)
