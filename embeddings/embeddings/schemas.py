from typing import List, Optional

from pydantic import BaseModel, Field
import pydantic


class EmbedRequest(BaseModel):
    instances: Optional[List[str]] = Field(description="list of sentences")


class EmbedResultSchema(BaseModel):
    predictions: List[pydantic.conlist(float, min_items=512, max_items=512)] = Field(
       description="an array of embedding vectors"
    )

class EmbedQuestionResultSchema(BaseModel):
    predictions: pydantic.conlist(float, min_items=512, max_items=512) = Field(
       description="embedding vector for question. dimension = 512"
    )

class ResponseContext(BaseModel):
    sentence: str = Field(description="sentence text")
    context: str = Field(description="context text")

class EmbedResponseContextRequest(BaseModel):
    responses: List[ResponseContext] = Field(
       description="an array of sentences and their text context"
    )

class ResponseVector(BaseModel):
    sentence: str = Field(description="context sentence")
    encodings: pydantic.conlist(float, min_items=512, max_items=512) = Field(
       description="embedding vector for context sentence. dimension = 512"
    )

class EmbedResponseAnswerResultSchema(BaseModel):
    embedings: List[ResponseVector] = Field(
       description="an array of embedding vectors"
    )


