from typing import Dict, List, Optional

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Body
from aws_lambda_powertools import Logger

from api.settings import Settings
from api.services.retrieval import RETRIEVAL


SETTINGS = Settings()  # type: ignore - pulled from the environment
LOGGER = Logger(level=SETTINGS.log_level)

module_name = __name__.rsplit(".", maxsplit=1)[-1].replace("_", "-")
ROUTER = APIRouter(prefix=f"/{module_name}", tags=[module_name])


class QueryRequest(BaseModel):
    query: str
    top_k_override: Optional[int] = None
    minimum_threshold_override: Optional[float] = None


class QueryResult(BaseModel):
    id: str
    score: float
    metadata: Dict[str, str]


class QueryResponse(BaseModel):
    results: List[QueryResult]


@ROUTER.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest) -> QueryResponse:
    try:
        results = RETRIEVAL.query(request.query, request.top_k_override, request.minimum_threshold_override)

        return QueryResponse(
            results=[QueryResult(id=result.id, score=result.score, metadata=result.metadata) for result in results]
        )
    except Exception as e:
        LOGGER.error(f"Error during document query: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to query documents")
