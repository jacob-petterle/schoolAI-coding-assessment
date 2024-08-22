from typing import List, Dict, Any, Optional
import json

import numpy as np
from pydantic import BaseModel
import pinecone
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.parameters import get_secret

from api.settings import Settings
from api.boto3_clients import BEDROCK_CLIENT


logger = Logger()
    

class QueryResult(BaseModel):

    id: str
    score: float
    metadata: Dict[str, Any]


class Retrieval:

    def __init__(self, settings: Settings):
        self.index_name = settings.pinecone_host_name
        self._model_id = settings.embedding_model_id
        api_key = get_secret(settings.pinecone_api_key_secret_name)

        self.index = pinecone.Index(
            api_key=api_key,
            host=settings.pinecone_host_name,
        )

        self.top_k = settings.retrieval_top_k  # Assume this is set in your Settings class
        self.min_score = settings.retrieval_min_score  # Minimum similarity score to consider

    def query(self, query: str, retrieval_top_k_override: Optional[int] = None) -> List[QueryResult]:
        query_embedding = self._get_embedding(query)
        return self._query(query_embedding, retrieval_top_k_override)

    def _get_embedding(self, query: str) -> List[float]:
        body = {
            "inputText": query,
        }
        response = BEDROCK_CLIENT.invoke_model(
            body=json.dumps(body),
            contentType="application/json",
            accept="*/*",
            modelId=self._model_id,
        )
        response_body = json.loads(response.get("body").read())
        embedding = response_body["embedding"]
        return embedding

    def _query(self, query_vector: List[float], retrieval_top_k_override: Optional[int] = None) -> List[QueryResult]:
        logger.info(f"Querying Pinecone index '{self.index_name}'")

        results = self.index.query(vector=query_vector, top_k=retrieval_top_k_override or self.top_k, include_metadata=True)
        processed_results = [
            QueryResult(id=match.id, score=match.score, metadata=match.metadata)
            for match in results.matches
            if match.score >= self.min_score
        ]

        cut_off_index = self._elbow_method([r.score for r in processed_results])
        final_results = processed_results[: cut_off_index + 1]

        logger.info(f"Retrieved {len(final_results)} results after applying elbow method")
        return final_results

    def _elbow_method(self, scores: List[float], threshold: float = 0.05) -> int:
        if not scores:
            return 0

        scores = np.array(scores)
        n_points = len(scores)
        all_coords = np.vstack((range(n_points), scores)).T

        first_point = all_coords[0]
        line_vec = all_coords[-1] - all_coords[0]
        line_vec_norm = line_vec / np.sqrt(np.sum(line_vec**2))
        vec_from_first = all_coords - first_point

        scalar_prod = np.sum(vec_from_first * line_vec_norm, axis=1)
        vec_from_line = vec_from_first - np.outer(scalar_prod, line_vec_norm)
        dist_from_line = np.sqrt(np.sum(vec_from_line**2, axis=1))

        elbow_index = np.argmax(dist_from_line)

        # Check if the elbow point is significant enough
        if dist_from_line[elbow_index] < threshold * (scores[0] - scores[-1]):
            return n_points - 1  # Return all points if no significant elbow is found

        return elbow_index

RETRIEVAL = Retrieval(Settings())  # type: ignore - pulled from the environment
