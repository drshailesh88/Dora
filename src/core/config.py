"""Configuration management for Dora."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None

    # Local LLM
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    chroma_persist_dir: str = "./data/chroma"

    # Graph Database
    neo4j_uri: Optional[str] = None
    neo4j_user: str = "neo4j"
    neo4j_password: Optional[str] = None

    # Embeddings
    embedding_model: str = "NeuML/pubmedbert-base-embeddings"
    embedding_dimension: int = 768

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Retrieval
    dense_top_k: int = 20
    sparse_top_k: int = 20
    rrf_k: int = 60
    rerank_top_k: int = 10

    # Chunking
    chunk_size: int = 1024
    chunk_overlap: int = 150

    # EMR Integration
    emr_database_path: Optional[str] = None
    emr_sync_enabled: bool = False

    # Voice
    voice_enabled: bool = False
    wake_word: str = "hey_docassist"
    whisper_model: str = "base.en"

    # Licensing
    license_server_url: str = "https://license.docassist.in"
    telemetry_enabled: bool = True

    @property
    def has_cloud_llm(self) -> bool:
        """Check if any cloud LLM is configured."""
        return bool(self.openai_api_key or self.anthropic_api_key)

    @property
    def has_reranker(self) -> bool:
        """Check if Cohere reranker is configured."""
        return bool(self.cohere_api_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
