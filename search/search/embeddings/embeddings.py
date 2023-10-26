from __future__ import annotations

from enum import Enum
from typing import List
import requests


class OutputFormat(str, Enum):
    FLOAT_LIST = "float_list"
    STRING = "string"


class EmbeddingsRequest():
    output_format: OutputFormat = OutputFormat.FLOAT_LIST
    separator: str | None = None
    normalize: bool = True


class EmbeddingsTextRequest(EmbeddingsRequest):
    text: str


def get_embeduse_embeddings(sentences: list, embedUrl: str):
    r = requests.post(url=embedUrl, json={
                "instances": sentences})
    return r.json()['predictions']


def calculate_text_vectors(annotation_data: list, embedUrl: str):
    sentences = [x['text'] for x in annotation_data]
    return get_embeduse_embeddings(sentences, embedUrl)

