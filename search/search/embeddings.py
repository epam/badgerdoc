from __future__ import annotations
from enum import Enum
import requests
import openai
import json
from search.config import settings
from search.logger import logger
from typing import Any, Dict

LIMIT = 5


class OutputFormat(str, Enum):
    FLOAT_LIST = "float_list"
    STRING = "string"


class EmbeddingsRequest:
    output_format: OutputFormat = OutputFormat.FLOAT_LIST
    separator: str | None = None
    normalize: bool = True


class EmbeddingsTextRequest(EmbeddingsRequest):
    text: str


def get_sentence_embedding(sentence: str):
    r = get_sentences_embeddings([sentence], settings.embed_url)
    return r[0]


def get_sentences_embeddings(sentences: list, embedUrl: str):
    r = requests.post(url=embedUrl, json={"instances": sentences})
    return r.json()["predictions"]


def get_question_embedding(sentence: str):
    r = requests.get(url=f"{settings.embed_question_url}?question="+sentence)
    return r.json()["predictions"]


def calculate_text_vectors(annotation_data: list, embedUrl: str):
    sentences = [x["text"] for x in annotation_data]
    return get_sentences_embeddings(sentences, embedUrl)


def calculate_responses_embedings(sentences: list):
    r = requests.post(url=settings.embed_responses_url, json={"responses": [{"sentence": r, "context": c} for r, c in sentences]})
    return [x['encodings'] for x in r.json()["embedings"]]



async def get_gpt_opinion(contexts: list, query_str: str) -> Dict[str, Any]:
    """
       Sends combined pieces to LLM and returns answer in format : {"answer": ..., "context_number": ...}
       current limitation is first 5 pieces but to make based on token size.
       """
    if not query_str:
        return {}
    text_context = ""
    cnt = 0
    for i, piece in enumerate(contexts):
        if cnt < LIMIT and not piece in text_context:
            cnt += 1
            text_context += f"{i+1}. {piece}\n"

    if len(text_context)==0:
        return {}
    logger.info(f"context \n {text_context}")
    logger.info(len(text_context))
    openai.api_key = settings.chatgpt_api_key
    try:
        completion = openai.ChatCompletion.create(
            model=settings.chatgpt_model,
            messages=[
                {
                    "role": "system",
                    "content": """""",
                },
                {"role": "user", "content": (
                            f"Please provide short answer for this question and the most relevant context number: {query_str} \n based on these contexts: \n  {text_context}"
                            + "please provide answer in JSON format, like: {\"answer\": \"...\", \"context_number\":...}")
                 },
            ],
            frequency_penalty=0,
            temperature=0,
        )
        matches = completion.choices[0]["message"]["content"]
        if "answer" in matches:
            a_json = json.loads(matches)
            logger.info(f"gpt answer: {a_json['answer']}")
            return a_json

        return {}
    except Exception as e:
        print(e)
        return {}


async def get_gpt_opinion_stub(contexts: list, query_str: str) -> Dict[str, Any]:
    gpt_response = {
        "id": "chatcmpl-8LDuKlzkWzUlteOAfx50yaCPXX05o",
        "object": "chat.completion",
        "created": 1700069040,
        "model": "gpt-3.5-turbo-0613",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "{\"answer\": \"Two\", \"context_number\": 1}"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 284,
            "completion_tokens": 13,
            "total_tokens": 297
        }
    }
    matches = gpt_response["choices"][0]["message"]["content"]
    if "answer" in matches:
        a_json = json.loads(matches)
        logger.info(f"gpt answer: {a_json['answer']}")
        return a_json
    return {}
