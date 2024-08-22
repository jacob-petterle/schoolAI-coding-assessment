from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from aws_lambda_powertools import Logger

from api.settings import Settings
from api.routers.retrieval import QueryRequest, QueryResult
from api.services.chat import CHAT_SERVICE


SETTINGS = Settings()  # type: ignore - pulled from the environment
LOGGER = Logger(level=SETTINGS.log_level)

module_name = __name__.rsplit(".", maxsplit=1)[-1].replace("_", "-")
ROUTER = APIRouter(prefix=f"/{module_name}", tags=[module_name])


class ChatResponse(BaseModel):
    response: str
    relevancy: float
    supporting_docs: List[QueryResult]


@ROUTER.post("/chat", response_model=ChatResponse)
def chat(request: QueryRequest) -> ChatResponse:
    response, docs = CHAT_SERVICE.generate_response(request.query, request.top_k_override, request.minimum_threshold_override)
    converted_docs = []
    for doc in docs:
        converted_docs.append(QueryResult(id=doc.id, score=doc.score, metadata=doc.metadata))
    return ChatResponse(response=response.response, relevancy=response.relevancy, supporting_docs=converted_docs)
