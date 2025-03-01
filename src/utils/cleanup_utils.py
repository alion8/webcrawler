"""
Cleanup utilities for the web crawler.
"""
import logging
import random
from typing import Set, Tuple, List, Dict, Any

from pinecone import Pinecone

def scan_bad_vectors(
    index: Pinecone.Index, 
    vector_dim: int, 
    batch_size: int, 
    max_iterations: int,
    min_text_length: int,
    embedding_near_zero_epsilon: float
) -> Tuple[Set[str], int]:
    """
    Scan the entire Pinecone index using iterative random queries and flag vectors
    that fail quality checks. A vector is considered "bad" if:
      1. Its metadata is missing a 'text' field or the 'text' field is empty.
      2. Its 'text' field exists but its length is below min_text_length.
      3. Its embedding values are missing, not the correct dimension, or nearly all zero.
    
    Args:
        index: The Pinecone index instance.
        vector_dim: Expected dimensionality of the vectors.
        batch_size: Number of vectors to request per query call.
        max_iterations: Maximum iterations to perform.
        min_text_length: Minimum acceptable text length.
        embedding_near_zero_epsilon: Threshold for considering an embedding to be near zero.
        
    Returns:
        A tuple containing:
          - A set of bad vector IDs.
          - The total number of unique vectors scanned.
    """
    logger = logging.getLogger(__name__)
    seen_ids = set()
    bad_ids = set()
    iteration = 0

    # Filter that always matches all vectors.
    all_filter = {"$or": [{"text": {"$eq": ""}}, {"text": {"$ne": ""}}]}

    while iteration < max_iterations:
        iteration += 1
        # Generate a new random query vector each iteration.
        random_vector = [random.random() for _ in range(vector_dim)]
        try:
            response = index.query(
                vector=random_vector,
                top_k=batch_size,
                include_metadata=True,
                include_values=True,
                filter=all_filter
            )
        except Exception as e:
            logger.error(f"Error during query on iteration {iteration}: {e}")
            break

        matches = response.get("matches", [])
        new_found = 0

        for match in matches:
            vid = match.get("id")
            if vid in seen_ids:
                continue
            seen_ids.add(vid)
            new_found += 1

            bad = False
            metadata = match.get("metadata", {})
            text_value = metadata.get("text", None)
            if text_value is None or text_value.strip() == "":
                bad = True
                logger.debug(f"Vector {vid} marked as bad: missing text.")
            elif len(text_value.strip()) < min_text_length:
                bad = True
                logger.debug(f"Vector {vid} marked as bad: text length {len(text_value.strip())} is below threshold {min_text_length}.")

            values = match.get("values", None)
            if values is None or len(values) != vector_dim:
                bad = True
                logger.debug(f"Vector {vid} marked as bad: missing or incorrect dimension in values.")
            else:
                if sum(abs(x) for x in values) < embedding_near_zero_epsilon:
                    bad = True
                    logger.debug(f"Vector {vid} marked as bad: embedding nearly zero.")

            if bad:
                bad_ids.add(vid)

        logger.info(f"Iteration {iteration}: Found {new_found} new vectors; total unique seen: {len(seen_ids)}.")
        if new_found == 0:
            logger.info("No new vectors found in this iteration; ending scan.")
            break

    logger.info(f"Scanned {len(seen_ids)} unique vectors; found {len(bad_ids)} bad vectors.")
    return bad_ids, len(seen_ids)


def delete_vectors(index: Pinecone.Index, vector_ids: List[str]) -> bool:
    """
    Delete vectors from the Pinecone index.
    
    Args:
        index: The Pinecone index instance.
        vector_ids: List of vector IDs to delete.
        
    Returns:
        True if deletion was successful, False otherwise.
    """
    logger = logging.getLogger(__name__)
    try:
        delete_response = index.delete(ids=vector_ids)
        logger.info(f"Deleted {len(vector_ids)} vectors from the index.")
        return True
    except Exception as e:
        logger.error(f"Error deleting vectors: {e}")
        return False 