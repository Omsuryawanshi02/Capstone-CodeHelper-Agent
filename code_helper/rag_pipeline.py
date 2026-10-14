"""RAG pipeline implementation.

Implements the complete RAG pipeline in separate stages:
1. File ingestion - read every relevant .py file from target project
2. Chunking - split files into chunks with line-based boundaries
3. Embeddings - generate vectors using NVIDIA NIM
4. Vector storage - store vectors and metadata in Pinecone
5. Retrieval - embed questions and retrieve matching chunks

No LangChain or LlamaIndex. Custom implementation only.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import (
    validate_config,
    NVIDIA_EMBED_MODEL,
    PINECONE_INDEX_NAME,
    PINECONE_CLOUD,
    PINECONE_REGION,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage 1 - File ingestion
# ---------------------------------------------------------------------------

def discover_source_files(root_dir: str) -> List[str]:
    """Discover every relevant .py file in the target project.

    Args:
        root_dir: Root directory to search recursively.

    Returns:
        Sorted list of absolute file paths for .py files.
        Excludes .git, .venv, cache directories, and secrets.
    """
    excluded_dirs = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
        "node_modules",
    }

    discovered = []

    for root, dirs, files in os.walk(root_dir):
        # Filter out excluded directories in-place
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        for filename in files:
            if not filename.endswith(".py"):
                continue

            # Skip secret files
            if filename.startswith(".") and filename.endswith((".key", ".pem")):
                continue

            full_path = os.path.join(root, filename)
            discovered.append(full_path)

    return sorted(discovered)


def read_source_file(file_path: str) -> Optional[str]:
    """Read a source file with UTF-8 encoding.

    Args:
        file_path: Absolute path to the file.

    Returns:
        File contents as string, or None if unreadable.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        logger.warning(f"Could not read file: {file_path}")
        return None


# ---------------------------------------------------------------------------
# Stage 2 - Chunking
# ---------------------------------------------------------------------------

def chunk_code(
    filename: str,
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """Split source text into overlapping line-based chunks.

    Each chunk includes:
    - Stable chunk ID
    - Relative filename
    - Start line (1-based)
    - End line (1-based, inclusive)
    - Original text

    Args:
        filename: Relative filename for metadata.
        text: Source code text to chunk.
        chunk_size: Lines per chunk (default: 100).
        overlap: Overlap lines between chunks (default: 20).

    Returns:
        List of chunk dictionaries. Empty list for empty input.
    """
    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    lines = text.splitlines(keepends=True)
    if not lines:
        return []

    chunks = []
    total = len(lines)
    start = 0

    while start < total:
        end = min(start + chunk_size, total)
        chunk_text = "".join(lines[start:end])

        # Skip empty chunks
        if chunk_text.strip():
            chunk_id = f"{filename}:{start + 1}-{end}"
            chunks.append({
                "id": chunk_id,
                "filename": filename,
                "start_line": start + 1,
                "end_line": end,
                "text": chunk_text,
            })

        start += chunk_size - overlap

    return chunks


# ---------------------------------------------------------------------------
# Stage 3 - Embeddings (NVIDIA NIM via LiteLLM)
# ---------------------------------------------------------------------------

def embed_text(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a batch of texts using NVIDIA NIM.

    Uses nvidia/nemotron-3-embed-1b via LiteLLM.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (list of floats).

    Raises:
        RuntimeError: If embedding fails or returns invalid data.
    """
    if not texts:
        return []

    if not validate_config():
        raise RuntimeError("Missing required configuration for embeddings")

    from litellm import embedding

    try:
        result = embedding(
            model=f"nvidia_nim/{NVIDIA_EMBED_MODEL}",
            input=texts,
        )
    except Exception as e:
        raise RuntimeError(f"Embedding API call failed: {e}")

    if not result or not result.data:
        raise RuntimeError("Embedding API returned empty result")

    embeddings = [item.embedding for item in result.data]

    # Validate dimensions - NVIDIA nemotron-3-embed-1b produces 2048 dimensions
    expected_dim = 2048
    for i, emb in enumerate(embeddings):
        if len(emb) != expected_dim:
            raise RuntimeError(
                f"Embedding dimension mismatch: got {len(emb)}, expected {expected_dim}"
            )

    return embeddings


# ---------------------------------------------------------------------------
# Stage 4 - Vector storage (Pinecone serverless)
# ---------------------------------------------------------------------------

def get_pinecone_index():
    """Get or create the Pinecone serverless index.

    Creates the index with required configuration if it doesn't exist:
    - 2048 dimensions
    - Cosine similarity metric
    - AWS cloud
    - us-east-1 region

    Returns:
        Pinecone Index object.

    Raises:
        RuntimeError: If Pinecone operations fail.
    """
    if not validate_config():
        raise RuntimeError("Missing required configuration for Pinecone")

    from pinecone import Pinecone, ServerlessSpec

    api_key = os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=api_key)

    index_name = PINECONE_INDEX_NAME

    # Check if index exists
    existing = pc.list_indexes().names()

    if index_name not in existing:
        # Create new serverless index with required configuration
        pc.create_index(
            name=index_name,
            dimension=2048,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=PINECONE_CLOUD,
                region=PINECONE_REGION,
            ),
        )
        logger.info(f"Created Pinecone index: {index_name}")
    else:
        # Validate existing index configuration
        index_description = pc.describe_index(index_name)
        if index_description.dimension != 2048:
            raise RuntimeError(
                f"Existing index has dimension {index_description.dimension}, expected 2048"
            )

    return pc.Index(index_name)


def upsert_chunks(index, chunks: List[Dict[str, Any]]) -> int:
    """Upsert chunks into Pinecone with embeddings and metadata.

    Args:
        index: Pinecone Index object.
        chunks: List of chunk dicts from chunk_code().

    Returns:
        Number of successfully upserted vectors.
    """
    if not chunks:
        return 0

    # Generate embeddings for all chunk texts
    texts = [c["text"] for c in chunks]
    try:
        embeddings = embed_text(texts)
    except RuntimeError as e:
        logger.error(f"Embedding failed during upsert: {e}")
        return 0

    # Build vectors for Pinecone upsert
    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        vectors.append({
            "id": chunk["id"],
            "values": embedding,
            "metadata": {
                "filename": chunk["filename"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "text": chunk["text"],
            },
        })

    # Upsert in batches
    batch_size = 100
    total_upserted = 0

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        try:
            response = index.upsert(vectors=batch)
            total_upserted += response.get("upserted_count", 0)
        except Exception as e:
            logger.error(f"Pinecone upsert batch failed: {e}")

    return total_upserted


# ---------------------------------------------------------------------------
# Stage 5 - Retrieval
# ---------------------------------------------------------------------------

def retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Embed a natural-language query and retrieve matching chunks.

    Args:
        query: Natural-language query string.
        top_k: Number of top matches to retrieve (default: 5).

    Returns:
        List of match dicts with filename, line ranges, score, and text.
        Empty list if query is empty or no matches found.
    """
    if not query or not query.strip():
        return []

    if not validate_config():
        return []

    try:
        index = get_pinecone_index()
    except RuntimeError as e:
        logger.error(f"Pinecone index unavailable: {e}")
        return []

    # Embed query with the same model used for documents
    try:
        query_embeddings = embed_text([query])
    except RuntimeError as e:
        logger.error(f"Query embedding failed: {e}")
        return []

    query_vector = query_embeddings[0]

    # Query Pinecone
    try:
        response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            include_values=False,
        )
    except Exception as e:
        logger.error(f"Pinecone query failed: {e}")
        return []

    matches = response.get("matches", [])

    # Format results
    results = []
    for match in matches:
        metadata = match.get("metadata", {})
        results.append({
            "filename": metadata.get("filename", "unknown"),
            "start_line": metadata.get("start_line", 0),
            "end_line": metadata.get("end_line", 0),
            "score": match.get("score", 0.0),
            "text": metadata.get("text", ""),
        })

    return results


# ---------------------------------------------------------------------------
# High-level indexing orchestration
# ---------------------------------------------------------------------------

def index_project(root_dir: str) -> Dict[str, Any]:
    """Run the complete RAG indexing pipeline on a project.

    Stages:
    1. Discover source files
    2. Read files and chunk them
    3. Generate embeddings
    4. Store in Pinecone
    5. Report results

    Args:
        root_dir: Path to the target project directory.

    Returns:
        Dict with statistics about the indexing operation.
    """
    stats = {
        "files_discovered": 0,
        "files_read": 0,
        "chunks_created": 0,
        "vectors_upserted": 0,
        "errors": [],
    }

    # Stage 1: Discover files
    files = discover_source_files(root_dir)
    stats["files_discovered"] = len(files)

    # Stage 2: Read and chunk
    all_chunks = []
    for file_path in files:
        rel_path = os.path.relpath(file_path, root_dir)
        text = read_source_file(file_path)
        if text is None:
            stats["errors"].append(f"Could not read: {file_path}")
            continue
        stats["files_read"] += 1
        chunks = chunk_code(rel_path, text)
        all_chunks.extend(chunks)

    stats["chunks_created"] = len(all_chunks)

    if not all_chunks:
        return stats

    # Stage 3 & 4: Embed and store
    try:
        index = get_pinecone_index()
        stats["vectors_upserted"] = upsert_chunks(index, all_chunks)
    except RuntimeError as e:
        stats["errors"].append(str(e))

    return stats