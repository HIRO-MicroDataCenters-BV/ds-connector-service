from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_prefix="DS__",
        case_sensitive=False,
        extra="ignore",
    )

def get_settings() -> Settings:
    settings = Settings()
    return settings
