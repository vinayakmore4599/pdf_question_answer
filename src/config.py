"""Configuration management for the MCP PDF project."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Perplexity API configuration
    perplexity_api_key: str
    perplexity_api_url: str = "https://api.perplexity.ai/chat/completions"
    
    # PDF processing settings
    pdf_chunk_size: int = 4000  # Characters per chunk for large PDFs
    max_pdf_pages: Optional[int] = None  # None means no limit
    
    # RAG settings
    use_rag: bool = True  # Use RAG for efficient question answering
    rag_chunk_size: int = 1200  # Chunk size for RAG indexing
    rag_chunk_overlap: int = 200  # Overlap between chunks
    rag_top_k: int = 5  # Number of relevant chunks to retrieve per question
    embedding_model: str = "all-MiniLM-L6-v2"  # Fast and lightweight embedding model
    # Alternative models:
    # "all-mpnet-base-v2" - Better quality, slower
    # "multi-qa-MiniLM-L6-cos-v1" - Optimized for Q&A
    
    # MCP Server settings
    mcp_server_name: str = "pdf-qa-server"
    mcp_server_version: str = "1.0.0"
    
    # Output settings
    output_dir: Path = Path("output")
    pretty_print_json: bool = True
    
    # Model settings
    # Perplexity Sonar models (as of 2024-2026):
    # Online models (with search): "llama-3.1-sonar-small-128k-online", "llama-3.1-sonar-large-128k-online"
    # Chat models (no search): "llama-3.1-sonar-small-128k-chat", "llama-3.1-sonar-large-128k-chat"
    # Note: Check https://docs.perplexity.ai/guides/model-cards for current model names
    model_name: str = "sonar"  # Using chat model for document-only analysis
    temperature: float = 0.2
    max_tokens: int = 4000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure output directory exists
settings.output_dir.mkdir(exist_ok=True)
