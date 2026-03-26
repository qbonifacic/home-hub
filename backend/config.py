from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://qbot@localhost:5432/homehub"

    # Auth
    secret_key: str = "change-me"
    dj_password: str = "wolfpack2026"
    wife_password: str = "wolfpack2026"
    q_api_key: str = "change-me"

    # Claude API
    anthropic_api_key: str = ""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Weather
    weather_lat: float = 40.5853
    weather_lon: float = -105.0844

    # Server
    port: int = 8400

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
