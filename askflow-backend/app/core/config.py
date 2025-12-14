from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, field_validator, ValidationInfo
from typing import Optional, Any

class Settings(BaseSettings):
    PROJECT_NAME: str = "AskFlow API"
    API_V1_STR: str = "/api/v1"
    
    # DATABASE
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    
    # LLM CONFIG
    LLM_PROVIDER: str = "openai" # "openai" or "azure"

    # Standard OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Azure OpenAI
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: Optional[str] = "2023-05-15"
    AZURE_EMBEDDING_DEPLOYMENT_NAME: Optional[str] = None
    
    # Computed Database URL
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_HOST"),
            port=info.data.get("POSTGRES_PORT"),
            path=info.data.get("POSTGRES_DB"),
        )

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
