import os

from dotenv import load_dotenv

load_dotenv()

KEYCLOAK_ENDPOINT = os.getenv(
    "KEYCLOAK_DIRECT_ENDPOINT", "http://dev2.badgerdoc.com"
)
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_ROLE_ADMIN = os.getenv("KEYCLOAK_ROLE_ADMIN", "")
KEYCLOAK_USERS_PUBLIC_KEY = os.getenv("KEYCLOAK_USERS_PUBLIC_KEY", "")

BADGERDOC_CLIENT_SECRET = os.getenv(
    "BADGERDOC_CLIENT_SECRET", "219367e9-d55a-4b15-8903-0d89fde7574e"
)
ADMIN_CLIENT_SECRET = os.getenv(
    "ADMIN_CLIENT_SECRET", "5aaae332-b24d-45b6-b2ea-f5949f0c95ae"
)

# Minio settings.
MINIO_URI = os.getenv("MINIO_URI", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

# app settings.
ROOT_PATH = os.getenv("ROOT_PATH", "")
