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
