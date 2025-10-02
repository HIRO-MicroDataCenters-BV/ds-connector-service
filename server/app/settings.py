from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CHUNK_SIZE: int
    MAX_FILE_SIZE: int
    MAX_FILES_TO_LIST: int
    FS_BASE_PATH: str

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
