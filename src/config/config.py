"""
Configuration module for the web crawler.
"""
import os
import logging
from typing import List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

@dataclass
class Config:
    """Configuration class for the web crawler."""
    # Environment Variables
    pinecone_api_key: str = field(default_factory=lambda: os.getenv("PINECONE_API_KEY"))
    pinecone_environment: str = field(default_factory=lambda: os.getenv("PINECONE_ENVIRONMENT"))
    pinecone_index_name: str = field(default_factory=lambda: os.getenv("PINECONE_INDEX_NAME"))
    pinecone_index_host: str = field(default_factory=lambda: os.getenv("PINECONE_INDEX_HOST"))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    embed_model: str = field(default_factory=lambda: os.getenv("EMBED_MODEL", "text-embedding-ada-002"))
    embedding_dimension: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSION", "1536")))
    
    # Script Configuration
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1000")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "200")))
    pdf_chunk_size: int = field(default_factory=lambda: int(os.getenv("PDF_CHUNK_SIZE", "1000")))
    pdf_chunk_overlap: int = field(default_factory=lambda: int(os.getenv("PDF_CHUNK_OVERLAP", "0")))
    
    save_file: str = field(default_factory=lambda: os.getenv("SAVE_FILE", "processed_urls.json"))
    jsonl_file: str = field(default_factory=lambda: os.getenv("JSONL_FILE", "processed_data.jsonl"))
    openai_rate_limit_delay: float = field(default_factory=lambda: float(os.getenv("OPENAI_RATE_LIMIT_DELAY", "1.0")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "8191")))
    sitemap_url: str = field(default_factory=lambda: os.getenv("SITEMAP_URL", "https://www.example.com/sitemap.xml"))
    batch_size: int = field(default_factory=lambda: int(os.getenv("BATCH_SIZE", "50")))
    max_concurrent_requests: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")))
    request_timeout: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "10")))
    max_concurrent_embeddings: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_EMBEDDINGS", "5")))
    max_concurrent_upserts: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_UPSERTS", "5")))
    
    # Source Control
    use_sitemap: bool = field(default_factory=lambda: os.getenv("USE_SITEMAP", "False").lower() == "true")
    use_manual_urls: bool = field(default_factory=lambda: os.getenv("USE_MANUAL_URLS", "False").lower() == "true")
    manual_urls: List[str] = field(default_factory=lambda: [
        url.strip() for url in os.getenv("MANUAL_URLS", "").split(",") if url.strip()
    ])
    
    # Link-Based Crawling Settings
    use_start_url: bool = field(default_factory=lambda: os.getenv("USE_START_URL", "False").lower() == "true")
    start_url: Optional[str] = field(default_factory=lambda: os.getenv("START_URL", None))
    
    # Detailed Case Extraction Options
    use_case_details: bool = field(default_factory=lambda: os.getenv("USE_CASE_DETAILS", "False").lower() == "true")
    case_container_selector: Optional[str] = field(default_factory=lambda: os.getenv("CASE_CONTAINER_SELECTOR", None))


def initialize_logging() -> logging.Logger:
    """Configure and return a logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("crawler.log", encoding="utf-8")
        ]
    )
    return logging.getLogger(__name__)


def load_configuration() -> Config:
    """Load environment variables and return a Config object."""
    load_dotenv()
    config = Config()
    missing_required = []
    required_fields = [
        "pinecone_api_key",
        "pinecone_environment",
        "pinecone_index_name",
        "openai_api_key",
    ]
    for field_name in required_fields:
        if not getattr(config, field_name):
            missing_required.append(field_name)
    if missing_required:
        logger = logging.getLogger(__name__)
        logger.error(f"Missing required environment variables: {', '.join(missing_required)}")
        exit(1)
    return config 