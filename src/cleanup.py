"""
Cleanup module for the web crawler.
"""
import os
import logging
from dotenv import load_dotenv

from src.indexers.pinecone_init import initialize_pinecone, connect_to_index, get_index_dimension
from src.utils.cleanup_utils import scan_bad_vectors, delete_vectors

# -------------------- Configuration -------------------- #

def load_cleanup_config():
    """Load and validate cleanup configuration from environment variables."""
    # Load environment variables from .env file
    load_dotenv()

    # Pinecone configuration from environment variables
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

    # Quality settings (from .env)
    min_text_length = int(os.getenv("MIN_TEXT_LENGTH", "50"))
    embedding_near_zero_epsilon = float(os.getenv("EMBEDDING_NEAR_ZERO_EPSILON", "1e-6"))
    max_iterations = int(os.getenv("MAX_ITERATIONS", "100"))
    batch_size = int(os.getenv("SCAN_BATCH_SIZE", "1000"))

    # Validate required variables
    missing_vars = [
        var_name for var_name, var_value in [
            ("PINECONE_API_KEY", pinecone_api_key),
            ("PINECONE_ENVIRONMENT", pinecone_environment),
            ("PINECONE_INDEX_NAME", pinecone_index_name)
        ] if not var_value
    ]
    
    if missing_vars:
        raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}. Please check your .env file.")
    
    return {
        "pinecone_api_key": pinecone_api_key,
        "pinecone_environment": pinecone_environment,
        "pinecone_index_name": pinecone_index_name,
        "min_text_length": min_text_length,
        "embedding_near_zero_epsilon": embedding_near_zero_epsilon,
        "max_iterations": max_iterations,
        "batch_size": batch_size
    }

# -------------------- Logging Setup -------------------- #

def setup_logging():
    """Configure and return a logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

# -------------------- Main Execution -------------------- #

def main():
    """Main execution function for the cleanup utility."""
    # Setup logging
    logger = setup_logging()
    
    try:
        # Load configuration
        config = load_cleanup_config()
        
        # Initialize Pinecone
        pinecone_client = initialize_pinecone(
            config["pinecone_api_key"], 
            config["pinecone_environment"]
        )
        if not pinecone_client:
            logger.error("Failed to initialize Pinecone client. Exiting.")
            return
        
        # Connect to index
        index = connect_to_index(pinecone_client, config["pinecone_index_name"])
        if not index:
            logger.error("Failed to connect to Pinecone index. Exiting.")
            return
        
        # Get index dimension
        vector_dim = get_index_dimension(index)
        if not vector_dim:
            logger.error("Failed to get index dimension. Exiting.")
            return
        
        # Scan for bad vectors
        logger.info("Starting full scan of Pinecone index for bad vectors...")
        bad_ids, total_scanned = scan_bad_vectors(
            index=index,
            vector_dim=vector_dim,
            batch_size=config["batch_size"],
            max_iterations=config["max_iterations"],
            min_text_length=config["min_text_length"],
            embedding_near_zero_epsilon=config["embedding_near_zero_epsilon"]
        )
        logger.info(f"Final scan result: Scanned {total_scanned} unique vectors; found {len(bad_ids)} bad vectors.")
        
        # Prompt for deletion
        if bad_ids:
            answer = input(f"Do you want to delete these {len(bad_ids)} bad vectors? (y/n): ").strip().lower()
            if answer == "y":
                success = delete_vectors(index, list(bad_ids))
                if success:
                    logger.info(f"Successfully deleted {len(bad_ids)} bad vectors from the index.")
                else:
                    logger.error("Failed to delete bad vectors.")
            else:
                logger.info("Deletion aborted by user.")
        else:
            logger.info("No bad vectors found; nothing to delete.")
            
    except Exception as e:
        logger.error(f"An error occurred during cleanup: {e}")
        return

if __name__ == "__main__":
    main() 