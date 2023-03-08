import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

KAFKA_BOOTSTRAP_SERVER = os.environ.get("KAFKA_BOOTSTRAP_SERVER")
KAFKA_SEARCH_TOPIC = os.environ.get("KAFKA_SEARCH_TOPIC")

producers = {}
