"""
Text processing utilities for the web crawler.
"""
import re
import io
from typing import List
from bs4 import BeautifulSoup
import pdfplumber
import tiktoken

# Initialize tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    return len(tokenizer.encode(text))

def clean_text(text: str) -> str:
    """Clean and normalize whitespace and punctuation."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r",{2,}", ",", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text

def extract_text_from_html(html_content: str) -> str:
    """
    Extract full visible text from HTML content.
    Only removes non-content tags.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return clean_text(text)

def extract_case_sections(html_content: str) -> str:
    """
    Heuristically extract case sections by collecting the text of parent
    containers of header tags that include common case keywords.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    sections = []
    keywords = ["facts", "issue", "held", "discussion", "citation"]
    for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        header_text = header.get_text(separator=" ", strip=True).lower()
        if any(kw in header_text for kw in keywords):
            parent = header.find_parent()
            if parent:
                sections.append(parent.get_text(separator="\n", strip=True))
    if sections:
        return clean_text("\n\n".join(sections))
    else:
        return extract_text_from_html(html_content)

def extract_case_details(html_content: str, selector: str = None) -> str:
    """
    Attempt to extract detailed case information.
    If a CSS selector is provided and matches, return that container's text;
    otherwise use heuristic extraction.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    if selector:
        container = soup.select_one(selector)
        if container:
            return clean_text(container.get_text(separator="\n", strip=True))
    return extract_case_sections(html_content)

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    full_text = "\n".join(text_parts)
    return clean_text(full_text)

def chunk_text_html(text: str, max_tokens: int, overlap: int) -> List[str]:
    """
    Chunk text into segments of max_tokens with overlap.
    This version uses token-based splitting.
    """
    tokens = tokenizer.encode(text)
    if len(tokens) <= max_tokens:
        return [text]
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_str = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_str)
        # Ensure we always move forward; if overlap >= max_tokens, move at least by one token.
        start += max_tokens - overlap if max_tokens - overlap > 0 else 1
    return chunks

def chunk_text_pdf(text: str, chunk_token_limit: int, overlap: int = 0) -> List[str]:
    """Chunk PDF text into segments of chunk_token_limit with overlap."""
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_token_limit, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_str = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_str)
        start = start + (chunk_token_limit - overlap) if overlap > 0 else end
    return chunks

def extract_links(html: str, base_url: str) -> List[str]:
    """Extract and resolve all anchor links from HTML based on a base URL."""
    import urllib.parse
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urllib.parse.urljoin(base_url, href)
        if full_url.startswith(base_url):
            links.append(full_url)
    return links 