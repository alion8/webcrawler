"""
Main execution module for the web crawler.
"""
import sys
import time
import asyncio
import logging

from src.config.config import Config, initialize_logging, load_configuration
from src.crawlers.page_crawler import crawl_start_url
from src.indexers.pinecone_indexer import Indexer

# Initialize logging
logger = initialize_logging()

# Load configuration
config = load_configuration()

# Set event loop policy for Windows
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logger.info("Set event loop policy to WindowsSelectorEventLoopPolicy.")
    except AttributeError as e:
        logger.error(f"Failed to set event loop policy: {e}")
        logger.info("Proceeding with default event loop policy.")

async def main_async():
    """
    Main asynchronous execution function.
    """
    tasks = []
    if config.use_start_url and config.start_url:
        tasks.append(crawl_start_url(config.start_url, config))
    if config.use_sitemap or config.use_manual_urls:
        indexer = Indexer(config, logger)
        tasks.append(indexer.run())
    if tasks:
        await asyncio.gather(*tasks)
    else:
        logger.error("No crawling method enabled. Please enable at least one of USE_START_URL, USE_SITEMAP, or USE_MANUAL_URLS.")

def main():
    """
    Main execution function.
    """
    start_time = time.time()
    asyncio.run(main_async())
    end_time = time.time()
    logger.info(f"Total runtime: {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main() 