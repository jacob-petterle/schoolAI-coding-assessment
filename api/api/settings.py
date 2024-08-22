from enum import Enum
from pydantic_settings import SettingsConfigDict, BaseSettings as PydanticBaseSettings


class ModelId(str, Enum):

    AMAZON_TITAN_EMBED_TEXT_V1 = "amazon.titan-embed-text-v1"
    AMAZON_TITAN_TEXT_EXPRESS_V1 = "amazon.titan-text-express-v1"


class Settings(PydanticBaseSettings):

    model_config = SettingsConfigDict(
        populate_by_name=True,
        env_file=".env",
        extra="ignore",
    )
    log_level: str = "DEBUG"
    s3_bucket_name: str
    embedding_model_id: str = ModelId.AMAZON_TITAN_EMBED_TEXT_V1
    pinecone_api_key_secret_name: str
    # Hardcoding because the pinecone construct doesn't expose the index name *yet*
    pinecone_host_name: str = "https://ragstack-index0-d41d8cd98f00b204e980-c6xn8rd.svc.apw5-4e34-81fa.pinecone.io"
    retrieval_top_k: int = 10
    retrieval_min_score: float = 0.0
    chat_model_id: str = ModelId.AMAZON_TITAN_TEXT_EXPRESS_V1
