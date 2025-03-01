"""
Pinecone indexer module for the web crawler.
"""
import asyncio
import logging
from typing import Set
import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from tqdm.asyncio import tqdm

import pinecone
from pinecone import Pinecone, ServerlessSpec

from src.config.config import Config
from src.utils.file_io import load_processed_urls
from src.crawlers.sitemap_crawler import fetch_sitemap_urls
from src.crawlers.page_crawler import scrape_batch_of_urls
from src.processors.content_processor import process_url_async

class Indexer:
    """
    Indexer class for managing the Pinecone index and processing URLs.
    """
    def __init__(self, config: Config, logger: logging.Logger):
        """
        Initialize the indexer.
        
        Args:
            config: The configuration object.
            logger: The logger to use.
        """
        self.config = config
        self.logger = logger
        self.processed_urls = load_processed_urls(config.save_file)
        self.index = self.initialize_pinecone_index()
        self.embed_semaphore = asyncio.Semaphore(config.max_concurrent_embeddings)
        self.upsert_semaphore = asyncio.Semaphore(config.max_concurrent_upserts)

    def initialize_pinecone_index(self) -> pinecone.Index:
        """
        Initialize the Pinecone index.
        
        Returns:
            The Pinecone index.
        """
        try:
            pinecone_instance = Pinecone(api_key=self.config.pinecone_api_key)
            existing_indexes = pinecone_instance.list_indexes()
            if self.config.pinecone_index_name not in existing_indexes.names():
                self.logger.info(f"Creating Pinecone index '{self.config.pinecone_index_name}'...")
                pinecone_instance.create_index(
                    name=self.config.pinecone_index_name,
                    dimension=self.config.embedding_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=self.config.pinecone_environment),
                )
                self.logger.info(f"Pinecone index '{self.config.pinecone_index_name}' created.")
            else:
                self.logger.info(f"Pinecone index '{self.config.pinecone_index_name}' already exists.")
            return pinecone_instance.Index(self.config.pinecone_index_name)
        except pinecone.PineconeException as e:
            self.logger.error(f"Failed to initialize Pinecone index: {e}")
            exit(1)

    async def process_url_async_wrapper(self, url: str, content: str):
        """
        Wrapper for process_url_async.
        
        Args:
            url: The URL to process.
            content: The content of the URL.
        """
        await process_url_async(
            url=url,
            content=content,
            index=self.index,
            config=self.config,
            embed_semaphore=self.embed_semaphore,
            upsert_semaphore=self.upsert_semaphore,
            processed_urls=self.processed_urls
        )

    async def run(self):
        """
        Run the indexer.
        """
        timeout = ClientTimeout(total=self.config.request_timeout)
        connector = TCPConnector(limit=self.config.max_concurrent_requests)
        async with ClientSession(timeout=timeout, connector=connector) as session:
            all_urls = []
            if self.config.use_sitemap:
                sitemap_urls = await fetch_sitemap_urls(session, self.config.sitemap_url, self.config)
                self.logger.info(f"Total URLs fetched from sitemap: {len(sitemap_urls)}")
                all_urls.extend(sitemap_urls)
            if self.config.use_manual_urls:
                self.logger.info(f"Using manual URL list with {len(self.config.manual_urls)} URLs")
                all_urls.extend(self.config.manual_urls)
            
            all_urls = list(set(all_urls))
            urls_to_process = [url for url in all_urls if url not in self.processed_urls]
            self.logger.info(f"URLs to process: {len(urls_to_process)}")
            
            total_batches = (len(urls_to_process) + self.config.batch_size - 1) // self.config.batch_size
            for i in range(0, len(urls_to_process), self.config.batch_size):
                batch = urls_to_process[i: i + self.config.batch_size]
                current_batch = i // self.config.batch_size + 1
                self.logger.info(f"Processing batch {current_batch} of {total_batches}: {len(batch)} URLs")
                
                scraped_results = await scrape_batch_of_urls(session, batch, self.config)
                processing_tasks = []
                
                for url, content in scraped_results.items():
                    if content:
                        task = self.process_url_async_wrapper(url, content)
                        processing_tasks.append(task)
                    else:
                        self.logger.warning(f"Skipping URL due to failed scraping: {url}")
                
                for task in tqdm(
                    asyncio.as_completed(processing_tasks),
                    total=len(processing_tasks),
                    desc="Processing URLs"
                ):
                    await task
        
        self.logger.info("Indexing process completed successfully.") 