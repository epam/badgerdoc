import os

import dotenv

dotenv.load_dotenv(dotenv.find_dotenv())

# General:
ROOT_PATH = os.getenv("ROOT_PATH", "")
KEYCLOAK_URI = os.getenv("KEYCLOAK_URI", "")
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT", "10"))
THRESHOLD_MUL = int(os.getenv("THRESHOLD_MUL", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))  # timeout in minutes

# Logger config:
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILEPATH = os.getenv("LOG_FILEPATH", "")

# Kafka config:
KAFKA_BOOTSTRAP_SERVER = os.environ["KAFKA_BOOTSTRAP_SERVER"]
KAFKA_CONSUME_TOPICS = os.environ["KAFKA_CONSUME_TOPICS"].split(",")
KAFKA_GROUP_ID = os.environ["KAFKA_GROUP_ID"]
KAFKA_TOPICS_PARTITIONS = os.environ["KAFKA_TOPICS_PARTITIONS"].split(",")
KAFKA_REPLICATION_FACTORS = os.environ["KAFKA_REPLICATION_FACTORS"].split(",")

# Database config:
POOL_SIZE = os.environ["SA_POOL_SIZE"]

DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_URL = os.environ["DB_URL"]

# Other:
TEST_MODE = os.getenv("TEST_MODE", "False").lower() in ("true", "1")
