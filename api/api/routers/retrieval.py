from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Body
from aws_lambda_powertools import Logger

from api.settings import Settings
from api.services.retrieval import RETRIEVAL


SETTINGS = Settings()  # type: ignore - pulled from the environment
LOGGER = Logger(level=SETTINGS.log_level)

module_name = __name__.rsplit(".", maxsplit=1)[-1].replace("_", "-")
ROUTER = APIRouter(prefix=f"/{module_name}", tags=[module_name])


class QueryRequest(BaseModel):

    query: str = Field(
        ...,
        title="The search query",
        description="The query string used to search for relevant documents.",
    )
    top_k_override: Optional[int] = Field(
        None,
        title="Top K override",
        description="An optional override for the number of top results to return.",
    )
    minimum_threshold_override: Optional[float] = Field(
        None,
        title="Minimum threshold override",
        description="An optional override for the minimum similarity threshold.",
    )


class QueryResult(BaseModel):

    id: str = Field(
        ...,
        title="Document ID",
        description="The unique identifier of the document.",
    )
    score: float = Field(
        ...,
        title="Relevance score",
        description="The relevance score of the document to the query.",
    )
    metadata: Dict[str, str] = Field(
        ...,
        title="Document metadata",
        description="Additional metadata associated with the document.",
    )


class QueryResponse(BaseModel):

    results: List[QueryResult] = Field(
        ...,
        title="Query results",
        description="A list of documents that match the search query.",
    )


@ROUTER.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest) -> QueryResponse:
    """
    Query documents based on the provided search query.

    This endpoint uses a retrieval system to find relevant documents based on
    the given query. It allows optional overrides for the number of results
    and the minimum similarity threshold.
    """
    try:
        results = RETRIEVAL.query(request.query, request.top_k_override, request.minimum_threshold_override)

        return QueryResponse(
            results=[QueryResult(id=result.id, score=result.score, metadata=result.metadata) for result in results]
        )
    except Exception as e:
        LOGGER.error(f"Error during document query: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to query documents")
