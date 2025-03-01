"""
Page crawler module for the web crawler.
"""
import os
import json
import logging
import random
import asyncio
from typing import Dict, List, Optional
import aiohttp
from aiohttp import ClientSession, ClientError, ClientTimeout

from src.config.config import Config
from src.utils.text_processing import extract_text_from_pdf, extract_links

async def scrape_page(session: ClientSession, url: str, config: Config) -> Optional[str]:
    """
    Scrape a page and return its content.
    
    Args:
        session: The aiohttp ClientSession to use for requests.
        url: The URL to scrape.
        config: The configuration object.
        
    Returns:
        The content of the page, or None if the page could not be scraped.
    """
    logger = logging.getLogger(__name__)
    retries = 5
    initial_delay = 1.0
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    for attempt in range(1, retries + 1):
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                ctype = response.headers.get("Content-Type", "").lower()
                if "application/pdf" in ctype or url.lower().endswith(".pdf"):
                    logger.info(f"Detected PDF content for {url}")
                    pdf_bytes = await response.read()
                    pdf_text = extract_text_from_pdf(pdf_bytes)
                    logger.info(f"Successfully extracted text from PDF {url}")
                    return pdf_text
                else:
                    text = await response.text()
                    logger.info(f"Successfully scraped HTML {url} ({len(text)} characters).")
                    return text
        except (ClientError, asyncio.TimeoutError) as e:
            if hasattr(e, "status") and e.status == 403:
                logger.warning(f"Received 403 error for {url}. Retrying with custom User-Agent header.")
                try:
                    async with session.get(url, headers=headers) as response:
                        response.raise_for_status()
                        ctype = response.headers.get("Content-Type", "").lower()
                        if "application/pdf" in ctype or url.lower().endswith(".pdf"):
                            logger.info(f"Detected PDF content for {url} with custom header")
                            pdf_bytes = await response.read()
                            pdf_text = extract_text_from_pdf(pdf_bytes)
                            logger.info(f"Successfully extracted text from PDF {url} with custom header")
                            return pdf_text
                        else:
                            text = await response.text()
                            logger.info(f"Successfully scraped HTML {url} with custom header ({len(text)} characters).")
                            return text
                except Exception as e2:
                    logger.error(f"Fallback with custom header failed for {url}: {e2}")
            if attempt < retries:
                delay = initial_delay * (2 ** (attempt - 1))
                jitter = random.uniform(0, 1)
                sleep_time = delay + jitter
                logger.warning(f"Attempt {attempt} for {url} failed: {e}. Retrying in {sleep_time:.2f} seconds...")
                await asyncio.sleep(sleep_time)
            else:
                logger.error(f"All {retries} attempts failed for {url}.")
    return None

async def scrape_batch_of_urls(session: ClientSession, urls: List[str], config: Config) -> Dict[str, Optional[str]]:
    """
    Scrape a batch of URLs and return their contents.
    
    Args:
        session: The aiohttp ClientSession to use for requests.
        urls: The URLs to scrape.
        config: The configuration object.
        
    Returns:
        A dictionary mapping URLs to their contents.
    """
    logger = logging.getLogger(__name__)
    results = {}
    tasks = [scrape_page(session, url, config) for url in urls]
    for url, task in zip(urls, asyncio.as_completed(tasks)):
        try:
            content = await task
            results[url] = content
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            results[url] = None
    return results

async def crawl_start_url(start_url: str, config: Config):
    """
    Scrape the start URL, extract links, then scrape each linked page and save results.
    
    Args:
        start_url: The URL to start crawling from.
        config: The configuration object.
    """
    logger = logging.getLogger(__name__)
    timeout = ClientTimeout(total=config.request_timeout)
    async with ClientSession(timeout=timeout) as session:
        logger.info(f"Scraping start URL: {start_url}")
        main_html = await scrape_page(session, start_url, config)
        if not main_html:
            logger.error("Failed to scrape the start URL.")
            return
        links = extract_links(main_html, start_url)
        logger.info(f"Found {len(links)} links on the start page.")
        results = {}
        for link in links:
            logger.info(f"Scraping linked URL: {link}")
            page_text = await scrape_page(session, link, config)
            if page_text:
                results[link] = page_text
            else:
                logger.warning(f"Failed to scrape linked URL: {link}")
        os.makedirs("json", exist_ok=True)
        with open("json/linked_pages.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        logger.info("Crawling of start URL complete. Results saved to json/linked_pages.json.") 