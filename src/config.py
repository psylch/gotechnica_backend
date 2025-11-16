from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Centralized application configuration driven by environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Cloudflare R2
    r2_account_id: Optional[str] = None
    r2_access_key_id: Optional[str] = None
    r2_secret_access_key: Optional[str] = None
    r2_bucket_name: Optional[str] = None
    r2_public_url: Optional[str] = None

    # DIFY API Keys
    dify_api_key_preprocessing: Optional[str] = None
    dify_api_key_card_gen: Optional[str] = None
    dify_api_key_qa: Optional[str] = None

    # Gemini
    gemini_api_key: Optional[str] = None

    # ElevenLabs
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None

    # Timeouts
    timeout_dify_preprocessing: int = 30
    timeout_dify_card_gen: int = 30
    timeout_gemini_highlight: int = 30
    timeout_elevenlabs_tts: int = 30
    timeout_dify_qa: int = 20

    # OpenRouter / Gemini via OpenRouter
    openrouter_api_key: Optional[str] = None
    openrouter_site_url: Optional[str] = None
    openrouter_site_name: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def r2_endpoint_url(self) -> Optional[str]:
        if self.r2_account_id:
            return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"
        return None


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
