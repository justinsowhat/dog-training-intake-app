from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    # Utilizing an optimized, high-performance free instruction-following tier
    MODEL_SLUG: str = "meta-llama/llama-3-8b-instruct:free"
    
    # Required OpenRouter analytics dashboard tracking headers
    APP_REFERER: str = "http://localhost:8000"
    APP_TITLE: str = "PawsitiveMind Dog Behavioral Consulting API"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./pawsitive_mind.db"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
settings = Settings()