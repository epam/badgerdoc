from django.test import TestCase, override_settings


def mock_db_and_file_storage(cls: type[TestCase]):
    return override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        STORAGES={
            "default": {
                "BACKEND": "django.core.files.storage.memory.InMemoryStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        },
    )(cls)
