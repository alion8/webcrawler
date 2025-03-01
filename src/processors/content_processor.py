"""
Content processor module for the web crawler.
"""
import asyncio
import logging
from typing import Optional, Set
from concurrent.futures import ThreadPoolExecutor

import openai
import pinecone

from src.config.config import Config
from src.utils.text_processing import (
    extract_text_from_html,
    extract_case_details,
    chunk_text_html,
    chunk_text_pdf
)
from src.utils.file_io import save_processed_urls, save_to_jsonl

# Global executor for running blocking operations
executor = ThreadPoolExecutor(max_workers=10)

async def embed_and_upsert_async(
    url: str,
    chunk_idx: int,
    chunk_text: str,
    index: pinecone.Index,
    config: Config,
    embed_semaphore: asyncio.Semaphore,
    upsert_semaphore: asyncio.Semaphore,
):
    """
    Generate an embedding for a chunk of text and upsert it into Pinecone.
    
    Args:
        url: The URL the chunk came from.
        chunk_idx: The index of the chunk.
        chunk_text: The text of the chunk.
        index: The Pinecone index to upsert into.
        config: The configuration object.
        embed_semaphore: Semaphore to limit concurrent embedding requests.
        upsert_semaphore: Semaphore to limit concurrent upsert requests.
    """
    logger = logging.getLogger(__name__)
    from src.utils.text_processing import count_tokens
    
    token_count = count_tokens(chunk_text)
    if token_count > config.max_tokens:
        logger.warning(f"Chunk {url}-{chunk_idx} exceeds max_tokens ({token_count}). Skipping.")
        return
    
    async with embed_semaphore:
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                executor,
                lambda: openai.Embedding.create(input=chunk_text, model=config.embed_model)
            )
            vector = response["data"][0]["embedding"]
            logger.info(f"Generated embedding for {url}-{chunk_idx}.")
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI embedding failed for {url}-{chunk_idx}: {e}")
            return
        except Exception as e:
            logger.error(f"Unexpected error during embedding for {url}-{chunk_idx}: {e}")
            return
    
    async with upsert_semaphore:
        try:
            loop = asyncio.get_event_loop()
            metadata = {"url": url, "chunk_index": chunk_idx, "text": chunk_text}
            vector_id = f"{url}-{chunk_idx}"
            await loop.run_in_executor(
                executor,
                lambda: index.upsert(vectors=[(vector_id, vector, metadata)])
            )
            logger.info(f"Upserted vector {vector_id} into Pinecone.")
            await loop.run_in_executor(
                executor,
                lambda: save_to_jsonl(
                    {"url": url, "chunk_index": chunk_idx, "text": chunk_text, "embedding": vector},
                    config.jsonl_file
                )
            )
        except pinecone.PineconeException as e:
            logger.error(f"Pinecone upsert failed for {url}-{chunk_idx}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during upsert for {url}-{chunk_idx}: {e}")

async def process_url_async(
    url: str,
    content: Optional[str],
    index: pinecone.Index,
    config: Config,
    embed_semaphore: asyncio.Semaphore,
    upsert_semaphore: asyncio.Semaphore,
    processed_urls: Set[str],
):
    """
    Process a URL by extracting text, chunking it, and generating embeddings.
    
    Args:
        url: The URL to process.
        content: The content of the URL.
        index: The Pinecone index to upsert into.
        config: The configuration object.
        embed_semaphore: Semaphore to limit concurrent embedding requests.
        upsert_semaphore: Semaphore to limit concurrent upsert requests.
        processed_urls: Set of URLs that have already been processed.
    """
    logger = logging.getLogger(__name__)
    
    if not content:
        logger.warning(f"No content to process for URL: {url}")
        return

    if url.lower().endswith(".pdf"):
        chunks = chunk_text_pdf(text=content, chunk_token_limit=config.pdf_chunk_size, overlap=config.pdf_chunk_overlap)
    else:
        if config.use_case_details:
            extracted_text = extract_case_details(content, config.case_container_selector)
        else:
            extracted_text = extract_text_from_html(content)
        chunks = chunk_text_html(text=extracted_text, max_tokens=config.max_tokens, overlap=config.chunk_overlap)

    tasks = []
    for idx, chunk in enumerate(chunks):
        task = embed_and_upsert_async(
            url=url,
            chunk_idx=idx,
            chunk_text=chunk,
            index=index,
            config=config,
            embed_semaphore=embed_semaphore,
            upsert_semaphore=upsert_semaphore
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    processed_urls.add(url)
    save_processed_urls(processed_urls, config.save_file)
    logger.info(f"Completed processing for URL: {url}") 