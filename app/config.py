"""Configuration management for the email processing application."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # LLM Configuration
    llm_provider: str = Field(default="ollama", env="LLM_PROVIDER")  # openai, gemini, ollama

    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")

    # Gemini Configuration
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-pro", env="GEMINI_MODEL")

    # Ollama Configuration
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3", env="OLLAMA_MODEL")

    # LLM General Settings
    llm_temperature: float = Field(default=0.1, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1000, env="LLM_MAX_TOKENS")
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_default_region: str = Field(default="us-east-1", env="AWS_DEFAULT_REGION")
    aws_endpoint_url: Optional[str] = Field(default=None, env="AWS_ENDPOINT_URL")
    
    # DynamoDB Configuration
    dynamodb_table_name: str = Field(default="email_processing_results", env="DYNAMODB_TABLE_NAME")
    
    # ChromaDB Configuration
    chroma_persist_directory: str = Field(default="./data/chroma", env="CHROMA_PERSIST_DIRECTORY")
    chromadb_host: str = Field(default="localhost", env="CHROMADB_HOST")
    chromadb_port: int = Field(default=8000, env="CHROMADB_PORT")
    chromadb_use_external: bool = Field(default=False, env="CHROMADB_USE_EXTERNAL")
    
    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    confidence_threshold: float = Field(default=0.85, env="CONFIDENCE_THRESHOLD")
    
    # PII Masking Configuration
    pii_mask_char: str = Field(default="*", env="PII_MASK_CHAR")
    pii_entities: List[str] = Field(
        default=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "SSN"],
        env="PII_ENTITIES"
    )
    
    # Domain matching weights
    exact_domain_weight: float = 1.0
    similar_domain_weight: float = 0.8
    default_domain_weight: float = 0.5
    
    # Email processing settings
    footer_lines_count: int = 3
    max_email_length: int = 10000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
