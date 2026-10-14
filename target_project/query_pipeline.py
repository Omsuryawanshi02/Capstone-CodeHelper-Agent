"""Query pipeline module for the target Python project.

Coordinates the RAG pipeline stages: retrieval, formatting,
and response generation for user queries about the codebase.

Wires together embedding, vector storage (Pinecone), and retrieval
to answer developer questions.
"""

from ..config import NVIDIA_EMBED_MODEL, validate_config


def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list:
    """Retrieve the top-k most relevant code chunks for a natural-language query.

    Stage 5 of the RAG pipeline: embed the query and retrieve matching chunks
    from Pinecone.

    Args:
        query: Natural-language question about the codebase.
        top_k: Number of top matches to retrieve (default: 5).

    Returns:
        List of dicts with keys: filename, start_line, end_line, score, text.
        Returns empty list if no matches found or configuration is missing.
    """
    if not query or not query.strip():
        return []

    if not validate_config():
        return []

    try:
        from litellm import embedding

        # Embed the query using the same model as documents
        embed_result = embedding(
            model=f"nvidia_nim/{NVIDIA_EMBED_MODEL}",
            input=query,
        )

        if not embed_result or not embed_result.data:
            return []

        query_embedding = embed_result.data[0].embedding

        # TODO: In full implementation, query Pinecone index here
        # For now, return empty since index may not be populated
        # matches = pinecone_index.query(vector=query_embedding, top_k=top_k, ...)
        # return matches

        return []  # Index not yet populated in initial setup

    except ImportError:
        return []
    except Exception as e:
        print(f"Error in retrieval: {e}")
        return []


def format_chunk_results(matches: list) -> str:
    """Format search results into a human-readable string.

    Args:
        matches: List of match dicts from Pinecone search.

    Returns:
        Formatted string with filenames, line ranges, scores, and text.
    """
    if not matches:
        return "No matching code chunks found."

    output_lines = []
    for i, match in enumerate(matches, 1):
        score = match.get("score", 0.0)
        metadata = match.get("metadata", {})
        filename = metadata.get("filename", "unknown")
        start_line = metadata.get("start_line", "?")
        end_line = metadata.get("end_line", "?")
        text = metadata.get("text", "")[:200]

        output_lines.append(
            f"{i}. File: {filename} | Lines: {start_line}-{end_line} | "
            f"Score: {score:.4f}\n   {text}..."
        )

    return "\n".join(output_lines)