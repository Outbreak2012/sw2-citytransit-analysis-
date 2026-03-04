from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CityTransit Analytics Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # ClickHouse
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 9000  # Puerto nativo de ClickHouse (no HTTP 8123)
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""
    CLICKHOUSE_DATABASE: str = "paytransit"
    
    # MongoDB
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USER: str = "admin"
    MONGODB_PASSWORD: str = "admin123"
    MONGODB_DATABASE: str = "paytransit"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redfire007"
    REDIS_DB: int = 0
    
    # Java Backend
    BACKEND_URL: str = "http://localhost:8080"
    BACKEND_API_KEY: Optional[str] = None
    
    # JWT
    JWT_SECRET: str = "your-secret-key-minimum-256-bits"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # ML Models
    MODEL_PATH: str = "./models"
    LSTM_MODEL_PATH: str = "./models/lstm_demand_prediction.h5"
    BERT_MODEL_PATH: str = "./models/bert_sentiment_analysis"
    
    # OpenAI / LangChain
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.7
    LANGCHAIN_VERBOSE: bool = True
    
    # Ollama (LLM Local - gratuito, sin API key)
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"  # Otros: mistral, codellama, phi3
    
    # Groq (API gratuita ultrarrápida)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"  # Otros: mixtral-8x7b, gemma-7b-it
    
    # HuggingFace (modelos open-source)
    HUGGINGFACE_API_KEY: Optional[str] = None
    HUGGINGFACE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"
    
    # LLM Provider Priority (ollama, groq, huggingface, openai)
    LLM_PROVIDER_PRIORITY: str = "ollama,groq,huggingface,openai"
    
    # PostgreSQL (para NL2SQL con el backend Java)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DATABASE: str = "paytransit"
    
    # Cache
    CACHE_TTL: int = 3600
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:4200",
        "http://localhost:8080",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
