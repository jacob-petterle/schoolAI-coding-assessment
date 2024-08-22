import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Path, File, UploadFile
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

from api.settings import Settings
from api.boto3_clients import S3_CLIENT

SETTINGS = Settings()  # type: ignore - pulled from the environment
LOGGER = Logger(level=SETTINGS.log_level)

module_name = __name__.rsplit(".", maxsplit=1)[-1].replace("_", "-")
ROUTER = APIRouter(prefix=f"/{module_name}", tags=[module_name])


@ROUTER.get("/{resource_id}", response_model=Dict[str, Any])
def get_resource(resource_id: str = Path(..., title="The ID of the resource to retrieve")) -> Dict[str, Any]:
    try:
        response = S3_CLIENT.head_object(Bucket=SETTINGS.s3_bucket_name, Key=resource_id)
        return {
            resource_id: {
                "filename": response["Metadata"].get("filename", "Unknown"),
                "size": response["Metadata"].get("size", "Unknown"),
                "indexing_status": response["Metadata"].get("indexing_status", "Unknown"),
            }
        }
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            raise HTTPException(status_code=404, detail="Resource not found")
        else:
            LOGGER.error(f"Error retrieving resource: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve resource")


@ROUTER.get("", response_model=List[Dict[str, str]])
def list_resources() -> List[Dict[str, str]]:
    try:
        response = S3_CLIENT.list_objects_v2(Bucket=SETTINGS.s3_bucket_name)
        return [{obj["Key"]: obj["Key"]} for obj in response.get("Contents", [])]
    except ClientError as e:
        LOGGER.error(f"Error listing resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list resources")


@ROUTER.post("", response_model=Dict[str, str])
def create_resource(file: UploadFile = File(...)) -> Dict[str, str]:
    try:
        resource_id = str(uuid.uuid4())
        contents = file.file.read()
        LOGGER.debug(f"Uploading file: {file.filename}, size: {len(contents)} bytes, resource_id: {resource_id}")
        S3_CLIENT.put_object(
            Bucket=SETTINGS.s3_bucket_name,
            Key=resource_id,
            Body=contents,
            ContentType=file.content_type,
            Metadata={"filename": file.filename, "size": str(len(contents))},
        )

        LOGGER.info(f"File uploaded: {file.filename}, size: {len(contents)} bytes, resource_id: {resource_id}")

        return {resource_id: file.filename}
    except Exception as e:
        LOGGER.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload file")


@ROUTER.delete("/{resource_id}", response_model=Dict[str, str])
def delete_resource(resource_id: str = Path(..., title="The ID of the resource to delete")) -> Dict[str, str]:
    try:
        # First, check the indexing status
        try:
            response = S3_CLIENT.head_object(Bucket=SETTINGS.s3_bucket_name, Key=resource_id)
            metadata = response.get("Metadata", {})
            indexing_status = metadata.get("indexing_status")

            if indexing_status != "COMPLETE":
                return {"message": "Resource is still being indexed and cannot be deleted at this time"}

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise HTTPException(status_code=404, detail="Resource not found")
            else:
                LOGGER.error(f"Error checking resource indexing status: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to check resource indexing status")

        # If indexing is complete, proceed with deletion
        S3_CLIENT.delete_object(Bucket=SETTINGS.s3_bucket_name, Key=resource_id)
        return {resource_id: "Deleted"}
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            raise HTTPException(status_code=404, detail="Resource not found")
        else:
            LOGGER.error(f"Error deleting resource: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete resource")
