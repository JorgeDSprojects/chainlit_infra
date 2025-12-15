from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "ChatMultiModel"
    DEBUG: bool = True
    
    # LLM Keys (De la Fase 2)
    OPENAI_API_KEY: str = "sk-..."
    OPENROUTER_API_KEY: str = "sk-..."
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"

    # AÑADIDO: Clave de autenticación para Chainlit (DEBE EXISTIR AQUÍ)
    CHAINLIT_AUTH_SECRET: str 

    class Config:
        env_file = ".env"

settings = Settings()
