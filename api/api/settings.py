from pydantic_settings import SettingsConfigDict, BaseSettings as PydanticBaseSettings


class Settings(PydanticBaseSettings):

    model_config = SettingsConfigDict(
        populate_by_name=True,
        env_file=".env",
        extra="ignore",
    )
    log_level: str = "DEBUG"
    s3_bucket_name: str
