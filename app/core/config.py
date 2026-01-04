import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic AI KB Bot"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # MongoDB
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "agentic_ai_kb"
    
    # Redis
    REDIS_URL: str
    
    # Vector DB
    FAISS_INDEX_PATH: str = "./data/vector/index.faiss"
    
    # Embeddings
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL_NAME: str = "gpt-3.5-turbo"

    
    # Storage
    STORAGE_TYPE: str = "local"
    LOCAL_STORAGE_PATH: str = "./data/storage"
    
    # Security
    SECRET_KEY: str = "insecure_default_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ENABLE_CHAT_HISTORY: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
