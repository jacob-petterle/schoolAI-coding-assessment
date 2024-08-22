from pydantic_settings import SettingsConfigDict, BaseSettings as PydanticBaseSettings


class Settings(PydanticBaseSettings):

    model_config = SettingsConfigDict(
        populate_by_name=True,
        env_file=".env",
        extra="ignore",
    )
    log_level: str = "DEBUG"
    s3_bucket_name: str
    pinecone_api_key_secret_name: str
    # Hardcoding because the pinecone construct doesn't expose the index name *yet*
    pinecone_index_name: str = "ragstack-index0-d41d8cd98f00b204e980"
