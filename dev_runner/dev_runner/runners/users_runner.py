from dev_runner.conf import settings

from .base_runner import BaseRunner


class UsersRunner(BaseRunner):
    PACKAGE_NAME = "users"
    PORT = settings.USERS_PORT
    APP_NAME = "users"
    DB_CREDENTIALS = {
        "POSTGRES_DB": "keycloak_db",
    }
    ENVIRONMENT = {
        "DB_VENDOR": "POSTGRES",
        "DB_ADDR": "postgres",
        "DB_DATABASE": "keycloak_db",
        "DB_USER": "postgres",
        "DB_PASSWORD": "postgres",
        "POSTGRES_HOST": "postgres",
        "KEYCLOAK_USER": "user",
        "KEYCLOAK_PASSWORD": "secretpassword",
        "KEYCLOAK_ENDPOINT": "http://localhost/",
        "KEYCLOAK_REALM": "master",
        "KEYCLOAK_ROLE_ADMIN": "admin",
        "KEYCLOAK_USERS_PUBLIC_KEY": "",
    }
