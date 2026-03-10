import os
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    redis_url: str = "redis://localhost:6379"
    redis_enabled: bool = True
    database_url: str = "sqlite:///./data/aegis.db"
    embedding_model: str = "all-MiniLM-L6-v2"
    default_domain: str = "general"
    log_level: str = "INFO"
    max_concurrent_verifications: int = 50
    entropy_sample_count: int = 5
    pii_redaction_enabled: bool = True

    class Config:
        env_file = ".env"


settings = Settings()

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def load_yaml(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def get_default_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "default.yaml")


def get_domain_config(domain: str | None = None) -> dict[str, Any]:
    domain = domain or settings.default_domain
    domain_path = CONFIG_DIR / "domains" / f"{domain}.yaml"
    if not domain_path.exists():
        domain_path = CONFIG_DIR / "domains" / "general.yaml"
    return load_yaml(domain_path)
