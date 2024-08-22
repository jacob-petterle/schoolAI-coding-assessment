import json
from typing import Dict, List, Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source

from indexer.services.extract import EXTRACT
from indexer.services.transform import TRANSFORM
from indexer.services.load import LOAD
from indexer.settings import Settings


SETTINGS = Settings()  # type: ignore - pulled from the environment

LOGGER = Logger(level=SETTINGS.log_level)


@LOGGER.inject_lambda_context(log_event=True)
@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, _: LambdaContext) -> Dict[str, Any]:
    LOGGER.debug(f"Processing SQS event: {event}")

    for record in event.records:
        # event_name = json.loads(record.body)["Records"][0]["eventName"]
        # body *ma* be a dict and not a list if only one record is sent need to handle both cases, in the case where it's not a list, the Records key is not present
        body = json.loads(record.body)
        if "Records" in body:
            event_name = json.loads(record.body)["Records"][0]["eventName"]
        else:
            event_name = json.loads(record.body)["Event"]
        LOGGER.info(f"Processing event: {event_name}")
        if event_name == "ObjectCreated:Put":
            put_vectors(event, _)
        elif event_name == "ObjectRemoved:DeleteMarkerCreated":
            delete_vectors(event, _)
        else:
            LOGGER.warning(f"Unsupported event: {event_name}")

    return {"statusCode": 200, "body": json.dumps({"message": "SQS event processed", "records": len(list(event.records))})}


def delete_vectors(event: SQSEvent, _: LambdaContext) -> None:
    for record in event.records:
        document_id = json.loads(record.body)["Records"][0]["s3"]["object"]["key"]
        LOGGER.info(f"Deleting vectors for document '{document_id}'")
        LOAD.delete_vectors(document_id)
        LOGGER.info(f"Deleted vectors for document '{document_id}'")


def put_vectors(event: SQSEvent, _: LambdaContext) -> None:
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

    LOAD.load(transformed_records)
    LOGGER.info(f"Loaded {len(transformed_records)} records into Pinecone")
