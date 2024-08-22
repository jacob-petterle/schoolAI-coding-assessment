from typing import List
from fastapi import APIRouter
from pydantic import BaseModel, Field
from aws_lambda_powertools import Logger

from api.settings import Settings
from api.routers.retrieval import QueryRequest, QueryResult
from api.services.chat import CHAT_SERVICE


SETTINGS = Settings()  # type: ignore - pulled from the environment
LOGGER = Logger(level=SETTINGS.log_level)

module_name = __name__.rsplit(".", maxsplit=1)[-1].replace("_", "-")
ROUTER = APIRouter(prefix=f"/{module_name}", tags=[module_name])


class ChatResponse(BaseModel):

    response: str = Field(
        ...,
        title="The generated response",
        description="The response generated by the chat service based on the input query.",
    )
    relevancy: float = Field(
        ...,
        title="The relevancy score",
        description="A score indicating the relevance of the generated response to the input query.",
    )
    supporting_docs: List[QueryResult] = Field(
        ...,
        title="The supporting documents",
        description="A list of supporting documents used to generate the response.",
    )


@ROUTER.post("/chat", response_model=ChatResponse)
def chat(request: QueryRequest) -> ChatResponse:
    """
    Generate a chat response based on the provided query.

    This endpoint uses a Retrieval-Augmented Generation (RAG) system to generate
    a response. It retrieves relevant documents based on the query and uses them
    to inform the generation of the response.
    """
    response, docs = CHAT_SERVICE.generate_response(request.query, request.top_k_override, request.minimum_threshold_override)
    converted_docs = []
    for doc in docs:
        converted_docs.append(QueryResult(id=doc.id, score=doc.score, metadata=doc.metadata))
    return ChatResponse(response=response.response, relevancy=response.relevancy, supporting_docs=converted_docs)
