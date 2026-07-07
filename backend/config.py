"""
Application configuration using pydantic-settings.
All values can be overridden via environment variables or .env file.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────
    app_name: str = "AI Email Response System"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # ── Server ─────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ── Database ────────────────────────────────────────────────
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/emails.db"

    # ── AI / LLM ────────────────────────────────────────────────
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 1024
    use_fallback_llm: bool = False  # set to True if no API key

    # ── Embeddings ──────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # ── FAISS ───────────────────────────────────────────────────
    faiss_index_path: str = str(BASE_DIR / "data" / "faiss.index")
    faiss_metadata_path: str = str(BASE_DIR / "data" / "faiss_meta.json")
    retrieval_top_k: int = 5

    # ── Evaluation ──────────────────────────────────────────────
    eval_weights: dict[str, float] = {
        "semantic_similarity": 0.30,
        "intent_match": 0.20,
        "completeness": 0.15,
        "tone_match": 0.10,
        "action_coverage": 0.10,
        "safety": 0.05,
        "grammar_quality": 0.05,
        "professionalism": 0.03,
        "length_penalty": 0.02,
    }

    # ── Dataset ─────────────────────────────────────────────────
    dataset_path: str = str(BASE_DIR / "dataset" / "emails.json")

    @computed_field  # type: ignore[misc]
    @property
    def has_gemini_key(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key != "")

    @computed_field  # type: ignore[misc]
    @property
    def data_dir(self) -> Path:
        d = BASE_DIR / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
