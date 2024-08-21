from pathlib import Path
from typing import List, Dict, Any

from indexer.schemas import RawData
from aws_lambda_powertools import Logger
from pyarrow import parquet as pq

from indexer.boto3_clients import S3_CLIENT
from indexer.settings import Settings


logger = Logger()


class Extract:

    def __init__(self, settings: Settings):
        self.s3_bucket_name = settings.s3_bucket_name

    def extract(self, s3_keys: List[str]) -> List[RawData]:
        failed_records = []
        extracted_records = []
        for s3_key in s3_keys:
            try:
                local_path = self._download_from_s3(s3_key)
                records = self._from_parquet(local_path)
                for record in records:
                    raw_data = RawData.model_validate(record)
                    extracted_records.append(raw_data)
            except Exception as e:
                failed_records.append({"s3_key": s3_key, "error": str(e)})
        if failed_records and not extracted_records:
            logger.error(f"Failed to extract records: {failed_records}")
        elif failed_records:
            logger.warning(f"Failed to extract some records: {failed_records}")
        return extracted_records

    def _download_from_s3(self, s3_path: str) -> Path:
        local_path = Path(f"/tmp/{Path(s3_path).name}")
        S3_CLIENT.download_file(self.s3_bucket_name, s3_path, str(local_path))
        return local_path

    def _from_parquet(self, record: Path) -> List[Dict[str, Any]]:
        table = pq.read_table(record)
        return table.to_pylist()


EXTRACTOR = Extract(Settings())  # type: ignore - pulled from env
