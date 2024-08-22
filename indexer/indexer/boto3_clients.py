from boto3 import client
from botocore.config import Config

client_config = Config(
    max_pool_connections=300,
)

S3_CLIENT = client("s3")
BEDROCK_CLIENT = client("bedrock-runtime", config=client_config)
