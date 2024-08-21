import json
from typing import Dict, List, Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source

from indexer.services.extract import EXTRACT
from indexer.services.transform import TRANSFORM
from indexer.settings import Settings


SETTINGS = Settings()  # type: ignore - pulled from the environment

LOGGER = Logger(level=SETTINGS.log_level)


@LOGGER.inject_lambda_context(log_event=True)
@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, _: LambdaContext) -> Dict[str, Any]:
    LOGGER.debug(f"Processing SQS event: {event}")
    processed_records = []

    s3_keys = []
    for record in event.records:
        s3_keys.append(json.loads(record.body)["Records"][0]["s3"]["object"]["key"])

    LOGGER.info(f"Processing keys: {s3_keys}")
    extracted_records = EXTRACT.extract(s3_keys)
    LOGGER.info(f"Extracted {len(extracted_records)} records")
    LOGGER.debug(f"First 3 records: {extracted_records[:3]}")
    transformed_records = TRANSFORM.transform_data(extracted_records)
    LOGGER.info(f"Transformed {len(transformed_records)} records")
    LOGGER.debug(f"First 3 records: {transformed_records[:3]}")

    return {"statusCode": 200, "body": json.dumps({"message": "SQS event processed", "processed_records": processed_records})}
