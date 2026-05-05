from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Langfuse Config
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # GCP Config
    GOOGLE_APPLICATION_CREDENTIALS: str

    # OpenAI Config
    OPENAI_API_KEY: str
    
    # App Config
    DEBUG: bool = True
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
