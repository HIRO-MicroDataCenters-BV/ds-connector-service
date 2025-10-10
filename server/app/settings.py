from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CHUNK_SIZE: int = 8192  # 8KB chunks
    MAX_FILE_SIZE: int = 10737418240  # 10 * 1024 * 1024 * 1024  # 10GB limit
    MAX_FILES_TO_LIST: int = (
        10  # Limit for number of files to list in directory listings
    )
    FS_BASE_PATH: str = "./data"  # Base path for file system operations

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
