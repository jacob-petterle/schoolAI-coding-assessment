from typing import List

from indexer.schemas import RawData, TransformedData


class Transform:

    def transform_data(self, records: List[RawData]) -> List[TransformedData]:
        transformed_records = []
        for record in records:
            transformed_records.append(
                TransformedData(
                    question=record.question,
                    correct_answer=record.correct_answer,
                    support=record.support,
                )
            )
        return transformed_records

    def _get_embeddings(self, record: TransformedData) -> :
        # Placeholder for embedding logic
        return records