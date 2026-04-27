"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for CodeLens, loaded from .env file."""

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "codelens_dev"

    # LLM
    gemini_api_key: str = ""

    # JWT
    jwt_secret_key: str = "change_me_to_a_random_secret"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440

    # App
    log_level: str = "INFO"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
