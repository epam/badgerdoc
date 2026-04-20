import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import sentry_sdk

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "sample-api-key")

DEBUG = True


def add_address_to_allowed_hosts(
    address: str, allowed_hosts: list[str]
) -> None:
    if address.startswith(("http://", "https://")):
        parsed = urlparse(address)
        hostname = parsed.netloc
        if hostname:
            allowed_hosts.append(hostname)
    else:
        allowed_hosts.append(address)


BADGERDOC_ADDRESS = os.getenv("BADGERDOC_ADDRESS", "")
BADGERDOC_INTERNAL_ADDRESS = os.getenv("BADGERDOC_INTERNAL_ADDRESS", "")
ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

if BADGERDOC_ADDRESS:
    add_address_to_allowed_hosts(BADGERDOC_ADDRESS, ALLOWED_HOSTS)

if BADGERDOC_INTERNAL_ADDRESS:
    add_address_to_allowed_hosts(BADGERDOC_INTERNAL_ADDRESS, ALLOWED_HOSTS)

CSRF_TRUSTED_ORIGINS = []

for host in ALLOWED_HOSTS:
    for protocol in ["http", "https"]:
        origin = f"{protocol}://{host}"
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

BADGERDOC_DJANGO_APPS = [
    app_name.strip()
    for app_name in os.getenv("BADGERDOC_DJANGO_APPS", "").split(",")
    if app_name.strip()
]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_yasg",
    "storages",
    "badgerdoc",
    *BADGERDOC_DJANGO_APPS,
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


STATICFILES_DIRS = [
    BASE_DIR / "frontend/dist",
]

ROOT_URLCONF = "badgerdoc.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "badgerdoc.wsgi.application"


DB_ENGINE = os.getenv("BADGERDOC_DB_ENGINE", "sqlite")

if DB_ENGINE == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("BADGERDOC_DB_NAME", "badgerdoc"),
            "USER": os.getenv("BADGERDOC_DB_USER", "postgres"),
            "PASSWORD": os.getenv("BADGERDOC_DB_PASSWORD", ""),
            "HOST": os.getenv("BADGERDOC_DB_HOST", "localhost"),
            "PORT": os.getenv("BADGERDOC_DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }


def get_s3_storage_options() -> dict[str, Any]:
    s3_options: dict[str, Any] = {}

    bucket_name = os.getenv("BADGERDOC_OBJECT_STORAGE_BUCKET")
    if not bucket_name:
        logger.warning(
            "Bucket name is required. Set BADGERDOC_OBJECT_STORAGE_BUCKET environment variable"
        )
    s3_options["bucket_name"] = bucket_name

    access_key = os.getenv("BADGERDOC_OBJECT_STORAGE_ACCESS_KEY")
    secret_key = os.getenv("BADGERDOC_OBJECT_STORAGE_SECRET_KEY")
    if access_key and secret_key:
        s3_options["access_key"] = access_key
        s3_options["secret_key"] = secret_key

    endpoint_url = os.getenv("BADGERDOC_OBJECT_STORAGE_URL")
    if endpoint_url:
        s3_options["endpoint_url"] = endpoint_url

    region_name = os.getenv("BADGERDOC_OBJECT_STORAGE_REGION")
    if region_name:
        s3_options["region_name"] = region_name

    addressing_style = os.getenv(
        "BADGERDOC_OBJECT_STORAGE_ADDRESSING_STYLE", "path"
    )
    s3_options["addressing_style"] = addressing_style

    querystring_expire = int(
        os.getenv("BADGERDOC_OBJECT_STORAGE_QUERYSTRING_EXPIRE", "3600")
    )
    s3_options["querystring_expire"] = querystring_expire

    return s3_options


STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": get_s3_storage_options(),
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Basic": {"type": "basic"},
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"},
    },
    "USE_SESSION_AUTH": False,
    "JSON_EDITOR": True,
    "SUPPORTED_SUBMIT_METHODS": ["get", "post", "put", "delete", "patch"],
    "OPERATIONS_SORTER": "alpha",
    "TAGS_SORTER": "alpha",
    "DOC_EXPANSION": "none",
    "DEEP_LINKING": True,
    "SHOW_EXTENSIONS": True,
    "DEFAULT_MODEL_RENDERING": "model",
}

REDOC_SETTINGS = {
    "LAZY_RENDERING": False,
}

####################################################
#
# Badgerdoc settings
#
####################################################

BADGERDOC_LIFECYCLE_WORKFLOW_TYPE = os.getenv(
    "BADGERDOC_LIFECYCLE_WORKFLOW_TYPE", ""
)
BADGERDOC_LIFECYCLE_QUEUE = os.getenv("BADGERDOC_LIFECYCLE_DOCUMENT_QUEUE", "")

BADGERDOC_LIFECYCLE_TASK_WORKFLOW_TYPE = os.getenv(
    "BADGERDOC_LIFECYCLE_TASK_WORKFLOW_TYPE", ""
)
BADGERDOC_LIFECYCLE_TASK_QUEUE = os.getenv(
    "BADGERDOC_LIFECYCLE_TASK_QUEUE", ""
)

BADGERDOC_LIFECYCLE_EXTRACTION_WORKFLOW_TYPE = os.getenv(
    "BADGERDOC_LIFECYCLE_EXTRACTION_WORKFLOW_TYPE", ""
)
BADGERDOC_LIFECYCLE_EXTRACTION_QUEUE = os.getenv(
    "BADGERDOC_LIFECYCLE_EXTRACTION_QUEUE", ""
)

BADGERDOC_MAX_FILE_SIZE = int(os.getenv("BADGERDOC_MAX_FILE_SIZE", "0"))

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "")

####################################################
#
# Logging settings
#
####################################################

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "badgerdoc": {
            "handlers": ["console"],
            "level": os.getenv("BADGERDOC_LOG_LEVEL", "DEBUG"),
            "propagate": False,
        },
    },
}


####################################################
# Sentry configuration
# See: https://docs.sentry.io/platforms/python/integrations/django/
####################################################


def init_sentry():
    if sentry_sdk.is_initialized():
        return

    sentry_dsn = os.getenv("SENTRY_DSN", "")
    sentry_environment = os.getenv("SENTRY_ENVIRONMENT", "")
    if not sentry_dsn:
        logger.warning(
            "SENTRY_DSN environment variable is not set. Skipping Sentry initialization."
        )
        return

    if not sentry_environment:
        logger.warning("SENTRY_ENVIRONMENT environment variable is not set.")

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=sentry_environment,
        server_name=f"web-{sentry_environment}",
        send_default_pii=False,
    )
    logger.info(
        "Sentry has initialized on '%s' environment.", sentry_environment
    )


init_sentry()
