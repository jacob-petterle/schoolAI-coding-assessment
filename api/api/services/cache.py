import time
from typing import Any, Optional, Dict
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger
from api.settings import Settings
import boto3

logger = Logger()


class CacheService:

    def __init__(self, settings: Settings):
        self.table_name = settings.cache_table_name
        self.ttl_column_name = settings.cache_table_ttl_column_name
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)
        self._cache_value_key_name = "value"
        self._partition_key_column_name = settings.partition_key_column_name

    def get(self, key: str) -> Optional[str]:
        try:
            response = self.table.get_item(Key={self._partition_key_column_name: key})

            if "Item" not in response:
                return None
            item = response["Item"]
            current_time = int(time.time())
            ttl = int(item.get(self.ttl_column_name, 0))

            if ttl < current_time:
                logger.info(f"Cache item with key '{key}' has expired")
                return None

            item.pop(self.ttl_column_name, None)
            item.pop("key", None)
            return item[self._cache_value_key_name]

        except ClientError as e:
            logger.error(f"Error retrieving item from cache: {str(e)}")
            return None

    def set(self, key: str, value: str, ttl: int) -> None:
        try:
            expiration_time = int(time.time()) + ttl

            item = {
                self._cache_value_key_name: value,
                self._partition_key_column_name: key,
                self.ttl_column_name: expiration_time,
            }

            self.table.put_item(Item=item)
            logger.info(f"Successfully set cache item with key '{key}'")

        except ClientError as e:
            logger.error(f"Error setting item in cache: {str(e)}")


CACHE_SERVICE = CacheService(Settings())  # type: ignore - pulled from the environment
