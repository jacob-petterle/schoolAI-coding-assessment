from boto3 import client, resource


S3_CLIENT = client("s3")
BEDROCK_CLIENT = client("bedrock-runtime")
DYNAMODB_RESOURCE = resource("dynamodb")