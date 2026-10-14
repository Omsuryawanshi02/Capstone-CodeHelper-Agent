"""Vector store module for the target Python project.

Handles storage of code embeddings in Pinecone serverless index.

Provides deterministic ID generation and predictable upsert behavior
to prevent stale or duplicate records.
"""

import uuid
from typing import List, Dict, Any


def generate_vector_id(filename: str, start_line: int, end_line: int) -> str:
    """Generate a deterministic vector ID from chunk metadata.

    Args:
        filename: Relative filename.
        start_line: Start line number (1-based).
        end_line: End line number (1-based).

    Returns:
        Deterministic string ID suitable for Pinecone upserts.
    """
    # Use a hash-like deterministic ID from chunk metadata
    hash_input = f"{filename}:{start_line}:{end_line}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hash_input))


def upsert_vectors(index, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Upsert vectors into the Pinecone index.

    Uses predictable IDs and batch upsert to prevent stale or
    duplicate records where possible.

    Args:
        index: Pinecone Index object.
        vectors: List of vector dicts with keys:
            - id: string vector ID
            - values: list of float embedding values
            - metadata: dict with source text and metadata

    Returns:
        Pinecone upsert response.
    """
    if not vectors:
        return {"upserted_count": 0}

    # Batch upsert - Pinecone handles batching internally
    # but we ensure we don't send unreasonably large batches
    batch_size = 100
    results = []

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        try:
            response = index.upsert(vectors=batch)
            results.append(response)
        except Exception as e:
            # Log error but continue with remaining vectors
            print(f"Error upserting batch: {e}")
            results.append({"upserted_count": 0})

    total_upserted = sum(r.get("upserted_count", 0) for r in results)
    return {"upserted_count": total_upserted, "detail": "Batched upsert completed"}


def search_similar(index, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for similar vectors in the Pinecone index.

    Args:
        index: Pinecone Index object.
        query_vector: Embedding vector for the query.
        top_k: Number of top results to return (default: 5).

    Returns:
        List of match dicts with similarity scores and metadata.
    """
    try:
        response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            include_values=False,
        )
        return response.get("matches", [])
    except Exception as e:
        print(f"Error searching Pinecone: {e}")
        return []