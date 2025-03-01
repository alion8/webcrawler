"""
Pinecone initialization module for the web crawler.
"""
import logging
from typing import Optional, Tuple

from pinecone import Pinecone, PineconeException

def initialize_pinecone(api_key: str, environment: str) -> Optional[Pinecone]:
    """
    Initialize the Pinecone client.
    
    Args:
        api_key: The Pinecone API key.
        environment: The Pinecone environment.
        
    Returns:
        The Pinecone client, or None if initialization failed.
    """
    logger = logging.getLogger(__name__)
    try:
        pinecone_client = Pinecone(api_key=api_key, environment=environment)
        logger.info("Successfully initialized Pinecone client.")
        return pinecone_client
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone: {e}")
        return None

def connect_to_index(pinecone_client: Pinecone, index_name: str) -> Optional[Pinecone.Index]:
    """
    Connect to a Pinecone index.
    
    Args:
        pinecone_client: The Pinecone client.
        index_name: The name of the index to connect to.
        
    Returns:
        The Pinecone index, or None if connection failed.
    """
    logger = logging.getLogger(__name__)
    try:
        index = pinecone_client.Index(index_name)
        logger.info(f"Connected to Pinecone index '{index_name}'.")
        return index
    except Exception as e:
        logger.error(f"Failed to connect to Pinecone index '{index_name}': {e}")
        return None

def get_index_dimension(index: Pinecone.Index) -> Optional[int]:
    """
    Get the dimension of a Pinecone index.
    
    Args:
        index: The Pinecone index.
        
    Returns:
        The dimension of the index, or None if retrieval failed.
    """
    logger = logging.getLogger(__name__)
    try:
        index_stats = index.describe_index_stats()
        vector_dim = index_stats.get("dimension", None)
        if not vector_dim:
            logger.error("Unable to retrieve vector dimension from index stats.")
            return None
        logger.info(f"Vector dimensionality retrieved successfully: {vector_dim}.")
        return vector_dim
    except Exception as e:
        logger.error(f"Error retrieving index stats: {e}")
        return None 