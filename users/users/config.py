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

# S3 settings
S3_CREDENTIALS_PROVIDER = os.getenv("S3_CREDENTIALS_PROVIDER")
S3_PREFIX = os.getenv("S3_PREFIX", "")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
AWS_PROFILE = os.getenv("AWS_PROFILE")

# app settings.
ROOT_PATH = os.getenv("ROOT_PATH", "")
