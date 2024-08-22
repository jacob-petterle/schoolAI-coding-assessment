import json
from typing import List, Dict, Any, Optional, Tuple
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.parameters import get_secret

from api.settings import Settings
from api.boto3_clients import BEDROCK_CLIENT
from api.services.retrieval import RETRIEVAL, QueryResult
from api.services.cache import CACHE_SERVICE

logger = Logger()

class ChatService:

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model_id = settings.chat_model_id
        self._cache_ttl = 15

    def generate_response(
        self,
        query: str,
        retrieve_top_k_override: Optional[int] = None,
        minimum_threshold_override: Optional[float] = None,
    ) -> Tuple[str, List[QueryResult]]:
        relevant_docs = RETRIEVAL.query(query, retrieve_top_k_override, minimum_threshold_override)
        if cache_val := CACHE_SERVICE.get(query):
            logger.info(f"Cache hit for query: {query}")
            return cache_val, relevant_docs
        context = self._prepare_context(relevant_docs)
        prompt = self._prepare_prompt(query, context)
        response = self._generate_bedrock_response(prompt)
        CACHE_SERVICE.set(query, response, self._cache_ttl)
        return response, relevant_docs

    def _prepare_context(self, relevant_docs: List[QueryResult]) -> str:
        context_parts = []
        for doc in relevant_docs:
            context_parts.append(f"Possibly relevant information: {doc}")
        return "\n\n".join(context_parts)

    def _prepare_prompt(self, query: str, context: str) -> str:      
        prompt = f"""You are an advanced question answering system designed to provide accurate and relevant information based solely on the given context. Your primary directive is to maintain the highest standards of information accuracy and relevance.

        Context:
        {context}

        User query: {query}

        Instructions:
        1. Carefully analyze the provided context and the user's query.
        2. Determine if the context contains information that is directly relevant to answering the user's query.
        3. If the context contains relevant information:
        - Provide a clear and concise answer based ONLY on the information in the context.
        - Cite specific parts of the context to support your answer.
        4. If the context does NOT contain relevant information to answer the query:
        - Explicitly state: "I apologize, but I don't have enough relevant information in the provided context to answer this question accurately."
        - Do NOT attempt to answer the question using general knowledge or information outside the given context.

        Answer:
        """
        logger.info(f"Generated prompt: {prompt}")
        return prompt

    def _generate_bedrock_response(self, prompt: str) -> str:
        try:
            body = {
                "prompt": prompt,
                "max_gen_len": 500,
                "temperature": 0.4,
                "top_p": 0.9,
            }

            response = BEDROCK_CLIENT.invoke_model(
                body=json.dumps(body),
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json"
            )

            response_body = json.loads(response['body'].read())
            return response_body["generation"]

        except Exception as e:
            logger.error(f"Error generating response from Bedrock: {str(e)}")
            raise

# Initialize the ChatService
CHAT_SERVICE = ChatService(Settings())  # type: ignore - pulled from the environment
