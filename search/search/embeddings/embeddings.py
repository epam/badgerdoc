from __future__ import annotations

from enum import Enum
import requests
import json

class OutputFormat(str, Enum):
    FLOAT_LIST = "float_list"
    STRING = "string"


class EmbeddingsRequest:
    output_format: OutputFormat = OutputFormat.FLOAT_LIST
    separator: str | None = None
    normalize: bool = True


class EmbeddingsTextRequest(EmbeddingsRequest):
    text: str


def get_embeduse_embeddings(sentences: list, embedUrl: str):
    r = requests.post(url=embedUrl, json={"instances": sentences})
    return r.json()["predictions"]

def get_qa_embeduse_embeddings(sentence: str, embedUrl: str):
    print(embedUrl)
    r = requests.post(url=embedUrl, json={"text": sentence})
    print(r)
    return r.json()["predictions"]

def calculate_text_vectors(annotation_data: list, embedUrl: str):
    sentences = [x["text"] for x in annotation_data]
    return get_embeduse_embeddings(sentences, embedUrl)


def calculate_response_embedings(sentences: list, embedUrl: str):
    r = requests.post(url=embedUrl, json={"responses": [{"sentence": r, "context": c} for r, c in sentences]})
    return [x['encodings'] for x in r.json()["embedings"]]
