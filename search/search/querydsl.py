import search.embeddings as embeddings
from typing import Any, Dict, List, Optional, Union


def get_subquery_embed_txt(query_str) -> Dict[str, Any]:
    boost_by_txt_emb = embeddings.get_sentence_embedding(query_str)
    return {
        "knn": {"embedding": {"vector": boost_by_txt_emb, "k": 512}}
    }


def get_subquery_embed_qa_txt(query_str) -> Dict[str, Any]:
    boost_by_txt_emb = embeddings.get_question_embedding(query_str)
    return {
        "knn": {"resp_embedding": {"vector": boost_by_txt_emb, "k": 512}}
    }


def get_subquery_text_match(query_str) -> Dict[str, Any]:
    return {
        "match": {"content": {"query": query_str, "minimum_should_match": "81%"}}
    }


def get_filter_by_scope(scope) -> Dict[str, Any]:
    return {
        "term": {"is_annotation": (scope == "annotation")
                 }}
