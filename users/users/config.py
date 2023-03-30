import os

from dotenv import load_dotenv

load_dotenv()

KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_ROLE_ADMIN = os.getenv("KEYCLOAK_ROLE_ADMIN", "")
KEYCLOAK_SYSTEM_USER_SECRET = os.getenv("KEYCLOAK_SYSTEM_USER_SECRET", "")

# S3 settings
S3_PROVIDER = os.getenv("S3_PROVIDER")
S3_PREFIX = os.getenv("S3_PREFIX", "")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
AWS_PROFILE = os.getenv("AWS_PROFILE")

# app settings.
ROOT_PATH = os.getenv("ROOT_PATH", "")
