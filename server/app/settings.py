from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CHUNK_SIZE: int = 8192  # 8KB chunks
    MAX_FILE_SIZE: int = 10737418240  # 10 * 1024 * 1024 * 1024  # 10GB limit
    MAX_FILES_TO_LIST: int = (
        10  # Limit for number of files to list in directory listings
    )
    FS_BASE_PATH: str = "./data"  # Base path for file system operations

    # S3 Multipart Upload Settings
    S3_MIN_PART_SIZE: int = (
        5 * 1024 * 1024
    )  # 5MB minimum part size for S3 multipart upload

    # S3-Compatible Storage Settings (AWS S3, MinIO, etc.)
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_SESSION_TOKEN: Optional[str] = None
    S3_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    S3_PREFIX: str = ""
    S3_ENDPOINT_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


def get_settings() -> Settings:
    settings = Settings()
    return settings
