from concurrent.futures import ThreadPoolExecutor
from typing import List

import pinecone
from aws_lambda_powertools import Logger

# import get_secret from lambda_powertools:
from aws_lambda_powertools.utilities.parameters import get_secret

from indexer.schemas import TransformedDataWithEmbedding
from indexer.settings import Settings
from indexer.boto3_clients import S3_CLIENT


logger = Logger()


class Load:

    def __init__(self, settings: Settings):
        self.index_name = settings.pinecone_host_name
        self.bucket_name = settings.s3_bucket_name

        api_key = get_secret(settings.pinecone_api_key_secret_name)

        self.index = pinecone.Index(
            api_key=api_key,
            host=settings.pinecone_host_name,
        )

    def load(self, records: List[TransformedDataWithEmbedding]) -> None:
        logger.info(f"Loading {len(records)} records into Pinecone index '{self.index_name}'")

        upsert_data: List[tuple] = []
        for i, record in enumerate(records):
            metadata = record.model_dump(mode="json", exclude={"embedding"})
            vector = (self._get_vector_id(record.document_id, i), record.embedding, metadata)
            upsert_data.append(vector)

        batch_size = 100
        batches = [upsert_data[i : i + batch_size] for i in range(0, len(upsert_data), batch_size)]
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(self.index.upsert, vectors=batch) for batch in batches]
            for i, future in enumerate(futures):
                try:
                    future.result()
                    logger.info(f"Upserted batch {i + 1} of {len(batches)}")
                except Exception as e:
                    logger.error(f"Error upserting batch {i + 1}: {str(e)}")
        logger.info("Finished loading data into Pinecone index")
        self._update_object_metadata(records)
        logger.info("Updated S3 object metadata")

    def _update_object_metadata(self, records: List[TransformedDataWithEmbedding]) -> None:
        keys = set(record.document_id for record in records)
        for key in keys:
            try:
                response = S3_CLIENT.head_object(Bucket=self.bucket_name, Key=key)
                metadata = response.get('Metadata', {})
                metadata['indexing_status'] = 'COMPLETE'
                S3_CLIENT.copy_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    CopySource={'Bucket': self.bucket_name, 'Key': key},
                    Metadata=metadata,
                    MetadataDirective='REPLACE',
                )
                logger.info(f"Updated S3 object {key} with indexing status: COMPLETE")
            except Exception as e:
                logger.error(f"Failed to update S3 object metadata: {str(e)}")

    def delete_vectors(self, document_id: str) -> None:
        logger.info(f"Deleting vectors for document '{document_id}' from Pinecone index '{self.index_name}'")
        id_generator = self.index.list(prefix=document_id, limit=100)
        for ids in id_generator:
            self.index.delete(ids)

    def _get_vector_id(self, document_id: str, index: int) -> str:
        return f"{document_id}_{index}"


LOAD = Load(Settings())  # type: ignore - pulled from the environment
