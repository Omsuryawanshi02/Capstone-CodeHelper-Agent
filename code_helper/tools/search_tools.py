"""RAG search tool - embeds queries and queries Pinecone.

Responsible for Stage 5 of the RAG pipeline: embedding a natural-language
query and retrieving matching chunks from Pinecone.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

from ..config import NVIDIA_EMBED_MODEL, PINECONE_INDEX_NAME, validate_config
from pinecone import Pinecone


def rag_search(query: str) -> str:
    """Embed a query and retrieve top matches from Pinecone.

    Args:
        query: Natural-language query string.

    Returns:
        Formatted string with matching code chunks, filenames, line numbers,
        and similarity scores. Returns "No matches found." if no results.
    """
    if not query or not query.strip():
        return "Error: Empty query provided."

    if not validate_config():
        return "Error: Pinecone/NVIDIA configuration missing."

    try:
        # Initialize Pinecone client
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

        # Get or create the index
        index_name = PINECONE_INDEX_NAME
        if index_name not in pc.list_indexes().names():
            # Index doesn't exist yet - return no matches
            return f"Pinecone index '{index_name}' does not exist. Please index code first."

        index = pc.Index(index_name)

        # Embed the query using the required NVIDIA model
        # Using LiteLLM to access NVIDIA NIM embedding model
        from litellm import embedding

        embed_result = embedding(
            model=f"nvidia_nim/{NVIDIA_EMBED_MODEL}",
            input=query,
        )

        if not embed_result or not embed_result.data:
            return "Error: Embedding model returned no data."

        item = embed_result.data[0]
        query_embedding = item["embedding"] if isinstance(item, dict) else getattr(item, "embedding")

        # Query Pinecone for top matches
        # Retrieve top 5 matches initially as required
        results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
            include_values=False,
        )

        if not results.get("matches"):
            return "No matching code chunks found in Pinecone."

        # Format results
        output_lines = []
        for match in results["matches"]:
            filename = match.get("metadata", {}).get("filename", "unknown")
            line_start = match.get("metadata", {}).get("start_line", match.get("metadata", {}).get("line_start", "?"))
            line_end = match.get("metadata", {}).get("end_line", match.get("metadata", {}).get("line_end", "?"))
            score = match.get("score", 0.0)
            text = match.get("metadata", {}).get("text", "")

            output_lines.append(
                f"Score: {score:.4f} | File: {filename} | Lines: {line_start}-{line_end}\n"
                f"```python\n{text.strip()}\n```"
            )


        return "\n".join(output_lines)

    except ImportError as e:
        return f"Error: Missing dependency - {e}"
    except Exception as e:
        return f"Error during Pinecone search: {e}"