from typing import List
from pydantic import BaseModel


class RawData(BaseModel):

    question: str
    distractor3: str
    distractor1: str
    distractor2: str
    correct_answer: str
    support: str


class TransformedData(BaseModel):

    question: str
    correct_answer: str
    support: str


class TransformedDataWithEmbedding(BaseModel):

    question: str
    correct_answer: str
    support: str
    embedding: List[float]
