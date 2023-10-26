import json
from typing import Optional, Iterator
from zipfile import ZipFile
from search.embeddings.embeddings import calculate_text_vectors
from search.harvester_helper import prepare_es_document
from opensearchpy import OpenSearch, helpers
PATH_PRODUCTS_DATASET = "search/embeddings/data"
NAME_DATASET = "1.json"
EMBED_URL="http://localhost:8501/v1/models/model:predict"


def load_annotation_dataset_from_zip():
    with ZipFile(PATH_PRODUCTS_DATASET + "/" + NAME_DATASET + ".zip") as dataZip:
        with dataZip.open(NAME_DATASET, mode='r') as dataFile:
            products_dataset = json.load(dataFile)
    return products_dataset


def load_annotation_dataset():
    with open(PATH_PRODUCTS_DATASET + "/" + NAME_DATASET) as f:
        data = json.load(f)
        return data


def enrich_with_embeddings(dataset)-> Optional[Iterator[dict]]:
    print(dataset)
    for data in dataset:
        text_piece_object=data['objs']
        if isinstance(text_piece_object, list):
            text_vectors = calculate_text_vectors(text_piece_object, EMBED_URL)
            for idx, text_piece in enumerate(text_piece_object):
                try:
                    content = text_piece["text"]
                    text_piece["embedding"] = text_vectors[idx]
                except KeyError:
                    print("error!")
                    continue
                document_params = content, data['job_id'], int(data['file_id']), int(data['page_num'])
                if content:
                    text_piece = prepare_es_document(text_piece, *document_params)
                    yield {"_index": "badger-doc", "_id": 12, "_source": text_piece}


#### es

es = OpenSearch([{'host': 'localhost', 'port':9203}])

#### load test data set
annotation_dataset = load_annotation_dataset()

#### Use the embedding model to calculate vectors for all annotation texts
es_docs = enrich_with_embeddings(annotation_dataset)
#### run indexation
print(helpers.bulk(es,  list(es_docs)))

index = 'badger-doc'
doc_id = '2'
#document = {"document_id": 3, "page_number": 1, "content": "temp", "job_id": "1", "category": "string"}
#es.index(index=index, id=doc_id, body=document)
