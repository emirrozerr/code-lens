from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    secret_key: str = "change-me"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    redis_url: str = "redis://localhost:6379"
    database_url: str = "postgresql://codelens:password@localhost:5432/codelens"

    openai_api_key: str = ""
    gemini_api_key: str = ""

    github_webhook_secret: str = ""


settings = Settings()
