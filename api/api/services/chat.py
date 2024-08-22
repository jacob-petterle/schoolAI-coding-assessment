import json
from typing import List, Dict, Any
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.parameters import get_secret

from api.settings import Settings
from api.boto3_clients import BEDROCK_CLIENT
from api.services.retrieval import RETRIEVAL, QueryResult

logger = Logger()

class ChatService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model_id = settings.chat_model_id

    def generate_response(self, query: str) -> str:
        relevant_docs = RETRIEVAL.query(query)
        context = self._prepare_context(relevant_docs)
        prompt = self._prepare_prompt(query, context)
        response = self._generate_bedrock_response(prompt)
        return response

    def _prepare_context(self, relevant_docs: List[QueryResult]) -> str:
        context_parts = []
        for doc in relevant_docs:
            content = doc.metadata.get('content', '')
            if content:
                context_parts.append(f"Relevant information: {content}")
        return "\n\n".join(context_parts)

    def _prepare_prompt(self, query: str, context: str) -> str:      
        prompt = f"""You are an AI assistant. Use the following context and chat history to answer the user's query. \
        If the context doesn't contain relevant information, use your general knowledge to provide a helpful response. \
        
        Context: {context}
        
        User query: {query}
        """
        return prompt

    def _generate_bedrock_response(self, prompt: str) -> str:
        try:
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 500,
                }
            }

            response = BEDROCK_CLIENT.invoke_model(
                body=json.dumps(body),
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json"
            )

            response_body = json.loads(response['body'].read())
            return response_body['results'][0]['outputText']

        except Exception as e:
            logger.error(f"Error generating response from Bedrock: {str(e)}")
            raise

# Initialize the ChatService
CHAT_SERVICE = ChatService(Settings())  # type: ignore - pulled from the environment
