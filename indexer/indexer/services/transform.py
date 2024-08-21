from concurrent.futures import ThreadPoolExecutor
import json
from typing import List

from indexer.schemas import RawData, TransformedData, TransformedDataWithEmbedding
from indexer.boto3_clients import BEDROCK_CLIENT
from indexer.settings import Settings


class Transform:

    def __init__(self, settings: Settings):
        self._model_id = settings.embedding_model_id.value

    def transform_data(self, records: List[RawData]) -> List[TransformedDataWithEmbedding]:
        transformed_records = []
        for record in records:
            transformed_records.append(
                TransformedData(
                    question=record.question,
                    correct_answer=record.correct_answer,
                    support=record.support,
                )
            )
        transformed_records = self.generate_embeddings(transformed_records)
        return transformed_records

    def generate_embeddings(self, records: List[TransformedData]) -> List[TransformedDataWithEmbedding]:
        with ThreadPoolExecutor(max_workers=len(records)) as executor:
            transformed_records = list(executor.map(self._get_embedding, records))
        return transformed_records

    def _get_embedding(self, record: TransformedData) -> TransformedDataWithEmbedding:
        body = {
            "inputText": record.model_dump_json(),
        }
        response = BEDROCK_CLIENT.invoke_model(
            body=json.dumps(body),
            contentType="application/json",
            accept="*/*",
            modelId=self._model_id,
        )
        response_body = json.loads(response.get('body').read())
        embedding = response_body['embedding']
        with_embedding = TransformedDataWithEmbedding(
            question=record.question,
            correct_answer=record.correct_answer,
            support=record.support,
            embedding=embedding,
        )
        return with_embedding


TRANSFORM = Transform(Settings())  # type: ignore - pulled from the environment
