"""Configuration settings for Clarity Platform."""

from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./clarity.db"

    # Storage
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_dir: Path = Path("./data/storage")

    # S3 / MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "clarity-documents"
    s3_region_name: str = "us-east-1"

    # VLM Endpoint
    openai_api_base: str = "http://localhost:11434/v1"
    openai_api_key: str = "ollama"
    vlm_default_model: str = "qwen2.5vl:3b"
    vlm_thinking_model: str = "qwen3-vl:8b"
    vlm_disable_thinking: bool = True
    vlm_timeout_seconds: float = 300.0
    vlm_num_ctx: int = 16384

    # API / security
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    max_upload_size_mb: int = 25

    # Validation & Quality Gates
    confidence_threshold: float = 0.85
    max_flagged_fields_before_escalation: int = 2
    dual_run_temperature: float = 0.3
    arithmetic_tolerance: float = 0.02


settings = Settings()
