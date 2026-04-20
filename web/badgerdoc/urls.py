from pathlib import Path
from typing import cast

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


def serve_frontend(*_args):
    index_path = (
        Path(settings.STATIC_ROOT) / "badgerdoc-frontend" / "index.html"
    )
    return FileResponse(open(index_path, "rb"), content_type="text/html")


schema_view = get_schema_view(
    openapi.Info(
        title="BadgerDoc API",
        default_version="v2",
        description="BadgerDoc API - Document Processing & Workflow Management",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("badgerdoc/", include("badgerdoc.api_urls")),
    path("api-auth/", include("rest_framework.urls")),
    *[
        path(f"{app_name}/", include(f"{app_name}.api_urls"))
        for app_name in settings.BADGERDOC_DJANGO_APPS
    ],
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    path(
        "docs/", RedirectView.as_view(url="/docs/index.html", permanent=True)
    ),
    re_path(
        r"^docs/(?P<path>.+/)$",
        RedirectView.as_view(url="/docs/%(path)sindex.html", permanent=True),
    ),
    re_path(
        r"^docs/(?P<path>.*)$",
        serve,
        {"document_root": settings.BASE_DIR / "docs" / "site"},
    ),
    re_path(
        r"^ui/.*$",
        serve_frontend,
        name="frontend",
    ),
    path(
        "",
        RedirectView.as_view(url="/ui/", permanent=True),
        name="api-docs-home",
    ),
]


if settings.DEBUG:
    urlpatterns.extend(
        cast(
            "list",
            static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
        )
    )
    urlpatterns.extend(
        cast(
            "list",
            static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
        )
    )
