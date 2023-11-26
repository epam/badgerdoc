import fastapi
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import (FastAPI,
                     HTTPException,
                     status,
                     Depends,
                     Union)
import tensorflow_hub as hub

import numpy as np
import tensorflow as tf
import schemas

app = FastAPI(
    title=settings.app_title,
    version=settings.version,
    openapi_tags=tags,
    root_path=settings.root_path,
    dependencies=[],
)


if WEB_CORS := os.getenv("WEB_CORS", ""):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=WEB_CORS.split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )


embed_qa = hub.load("https://www.kaggle.com/models/google/universal-sentence-encoder/frameworks/TensorFlow2/variations/qa/versions/2")
embed = hub.load("https://www.kaggle.com/models/google/universal-sentence-encoder/frameworks/TensorFlow2/variations/universal-sentence-encoder/versions/2")
print("module loaded")


@app.post('/api/use',
            tags=["Embeddings"],
    summary="USE embeddings",
                   response_model=schemas.EmbedResultSchema
         )
def text_use(
        request: schemas.EmbedRequest
) -> Union[schemas.EmbedResultSchema, HTTPException]:
    texts = request.instances
    if not texts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="invalid parameters"
        )
    return schemas.EmbedResultSchema(predictions=np.array(embed(texts)).tolist())


@app.get('/api/use-question',
            tags=["Embeddings"],
    summary="USE embeddings for Question",
                   response_model=schemas.EmbedResultSchema
         )
def text_question(
        question: str
) -> Union[schemas.EmbedQuestionResultSchema, HTTPException]:
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="invalid parameters"
        )
    query_embedding = embed_qa.signatures['question_encoder'](tf.constant([question]))['outputs'][0]

    return schemas.EmbedQuestionResultSchema(predictions= np.array(query_embedding).tolist())


@app.post('/api/use-responses',
            tags=["Embeddings"],
    summary="USE embeddings for Context Sentences",
                   response_model=schemas.EmbedResponseAnswerResultSchema
         )
def text_response(request: schemas.EmbedResponseContextRequest) -> Union[schemas.EmbedResponseAnswerResultSchema, HTTPException]:
    responses = request.responses
    response_batch = [r.sentence for r in responses]
    context_batch = [c.context for c in responses]
    if not responses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="invalid parameters"
        )
    encodings = embed_qa.signatures['response_encoder'](
        input=tf.constant(response_batch),
        context=tf.constant(context_batch)
    )
    ret = []
    for batch_index, batch in enumerate(response_batch):
        ret.append(schemas.ResponseVector(sentence=batch, encodings=np.array(encodings['outputs'][batch_index]).tolist()));

    return schemas.EmbedResponseAnswerResultSchema(embedings=ret)



if __name__ == '__main__':
    app.run('0.0.0.0', 8080, debug=False)
