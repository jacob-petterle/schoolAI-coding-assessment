from enum import Enum
from pydantic_settings import SettingsConfigDict, BaseSettings as PydanticBaseSettings


class ModelId(str, Enum):

    AMAZON_TITAN_EMBED_TEXT_V1 = "amazon.titan-embed-text-v1"


class Settings(PydanticBaseSettings):

    model_config = SettingsConfigDict(
        populate_by_name=True,
        env_file=".env",
        extra="ignore",
    )
    log_level: str = "DEBUG"
    embedding_model_id: ModelId = ModelId.AMAZON_TITAN_EMBED_TEXT_V1
    s3_bucket_name: str
    pinecone_api_key_secret_name: str
    # Hardcoding because the pinecone construct doesn't expose the index name *yet*
    pinecone_index_name: str = "ragstack-index0-d41d8cd98f00b204e980"
