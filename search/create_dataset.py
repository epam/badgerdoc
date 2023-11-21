from typing import Optional, Iterator
from search.search.embeddings import calculate_text_vectors
from search.search.embeddings import calculate_responses_embedings
#from search.harvester_helper import prepare_es_document
from tqdm import tqdm
import csv
from opensearchpy import OpenSearch, helpers

PATH_PRODUCTS_DATASET = "data/"
NAME_DATASET = "doc_query_pairs.train.tsv"
#EMBED_URL = "http://localhost:3334/api/use"
#QA_EMBED_URL = "http://localhost:3334/api/use-responses"
EMBED_URL = "http://localhost:3335/api/use"
QA_EMBED_URL = "http://localhost:3335/api/use-responses"
NUM_RECORDS = 30
INDEX="local"
#NUM_RECORDS = 20
VECTORS_BATCH_SIZE = 10
ES_HOST="localhost"
#ES_PORT=9202
ES_PORT=9204

def load_annotation_dataset():
    data = []
    i = 0
    with open(PATH_PRODUCTS_DATASET + "/" + NAME_DATASET, encoding="utf-8") as f:
        rd = csv.reader(f, delimiter="\t", quotechar='"')
        batch = []
        for row in rd:
            i += 1
            batch.append(row[0])
            if i % VECTORS_BATCH_SIZE == 0:
                # this is temporary solution. TODO: need context
                sentences = [ x.rstrip() for x  in batch]
                piece = {
                    "file_id": str(i),
                    "page_num": "1",
                    "objs": [{"category": "3", "text": t} for t in sentences],
                    "job_id": f"{i}",
                }
                data.append(piece)
                batch = []
            if i % NUM_RECORDS == 0:
                return data
    return data


def enrich_with_embeddings(dataset) -> Optional[Iterator[dict]]:
    for data in tqdm(dataset):
        text_piece_object = data["objs"]
        if isinstance(text_piece_object, list):
            text_vectors = calculate_text_vectors(text_piece_object, EMBED_URL)
            sentences = zip([t["text"] for t in text_piece_object], [t["text"] for t in text_piece_object])
            response_embeddings = calculate_responses_embedings(sentences, QA_EMBED_URL)

            for idx, text_piece in enumerate(text_piece_object):
                try:
                    content = text_piece["text"]
                    text_piece["embedding"] = text_vectors[idx]
                    text_piece["resp_embedding"] = response_embeddings[idx]
                except KeyError:
                    print("error!")
                    continue
                document_params = (
                    content,
                    data["job_id"],
                    int(data["file_id"]),
                    int(data["page_num"]),
                )
                if content:
                    text_piece = prepare_es_document(text_piece, *document_params)
                    yield {"_index": INDEX, "_source": text_piece}

def prepare_es_document(document: dict, content: str, job: int, file: int, page: int):
    es_document = {
        "document_id": file,
        "page_number": page,
        "content": content,
        "job_id": job,
        "category": document["category"],
        "embedding": document.get("embedding"),
        "resp_embedding": document.get("resp_embedding")
    }

    return es_document

#### es
es = OpenSearch([{"host": ES_HOST, "port": ES_PORT}])

#### load test data set
annotation_dataset = load_annotation_dataset()

#### Use the embedding model to calculate vectors for all annotation texts
print("Computing embeddings for %d sentences" % len(annotation_dataset))
es_docs = enrich_with_embeddings(annotation_dataset)
#### run indexation

print(helpers.bulk(es, es_docs))

