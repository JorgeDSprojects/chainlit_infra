from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ChatMultiModel"
    DEBUG: bool = True

    # LLM Keys (Las llenaremos en el .env más adelante)
    OPENAI_API_KEY: str = "sk-..."
    OPENROUTER_API_KEY: str = "sk-..."
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"

    class Config:
        env_file = ".env"


settings = Settings()
