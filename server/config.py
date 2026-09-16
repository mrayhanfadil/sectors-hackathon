from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    sectors_api_key: str = ""
    sectors_base: str = "https://api.sectors.app/v2"
    cache_ttl: int = 14400  # 4h KV
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:3000,https://*.pages.dev,https://sektoral-report.pages.dev"
    cors_allow_origin_regex: str = r"https://.*\.pages\.dev"
    env: str = "development"
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def cors_list(self) -> list[str]:
        # strip wildcards - those go via regex, not literal match
        return [o.strip() for o in self.cors_origins.split(",") if o.strip() and "*" not in o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
