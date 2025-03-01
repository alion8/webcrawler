"""
Sitemap crawler module for the web crawler.
"""
import logging
from typing import List
import asyncio
from xml.etree import ElementTree
from aiohttp import ClientSession, ClientError

from src.config.config import Config

async def fetch_sitemap_urls(session: ClientSession, sitemap_url: str, config: Config) -> List[str]:
    """
    Fetch URLs from a sitemap.
    
    Args:
        session: The aiohttp ClientSession to use for requests.
        sitemap_url: The URL of the sitemap to fetch.
        config: The configuration object.
        
    Returns:
        A list of URLs found in the sitemap.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Fetching URLs from sitemap: {sitemap_url}")
    try:
        async with session.get(sitemap_url) as response:
            response.raise_for_status()
            content = await response.text()
    except ClientError as e:
        if hasattr(e, "status") and e.status == 403:
            logger.warning(f"Received 403 error for {sitemap_url}. Retrying with custom User-Agent header.")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            }
            try:
                async with session.get(sitemap_url, headers=headers) as response:
                    response.raise_for_status()
                    content = await response.text()
            except Exception as e2:
                logger.error(f"Failed to fetch sitemap with custom header: {e2}")
                return []
        else:
            logger.error(f"Failed to fetch sitemap: {e}")
            return []
    except Exception as e:
        logger.error(f"Unexpected error fetching sitemap: {e}")
        return []
    
    try:
        root = ElementTree.fromstring(content)
        namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [elem.text for elem in root.findall(".//ns:loc", namespaces)]
        logger.info(f"Found {len(urls)} URLs in sitemap.")
        return urls
    except ElementTree.ParseError as e:
        logger.error(f"Failed to parse sitemap XML: {e}")
    except Exception as e:
        logger.error(f"Unexpected error parsing sitemap: {e}")
    return [] 