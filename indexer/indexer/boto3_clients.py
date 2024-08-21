from boto3 import client


S3_CLIENT = client("s3")
BEDROCK_CLIENT = client("bedrock-runtime")
