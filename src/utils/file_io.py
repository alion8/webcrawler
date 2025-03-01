"""
File I/O utilities for the web crawler.
"""
import os
import json
from typing import Set, Dict, Any

def load_processed_urls(filepath: str) -> Set[str]:
    """Load processed URLs from a JSON file."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error decoding JSON from {filepath}: {e}")
                return set()
    return set()

def save_processed_urls(processed_urls: Set[str], filepath: str):
    """Save processed URLs to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(list(processed_urls), f)

def save_to_jsonl(data: Dict[str, Any], filepath: str):
    """Append data to a JSONL file."""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n") 