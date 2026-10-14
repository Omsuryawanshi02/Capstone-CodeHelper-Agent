"""Main entry point for the target Python project.

Demonstrates a typical Python project structure with configuration,
indexing, and query capabilities. This file can be run directly
or used as the application startup point.

Typical usage:

    python main.py
    # or
    python -m main
"""

import sys
from .config import get_config
from .indexer import discover_python_files, chunk_code
from .vector_store import generate_vector_id, upsert_vectors, search_similar
from .query_pipeline import retrieve_relevant_chunks, format_chunk_results


def main():
    """Main function - demonstrate project capabilities."""
    print(f"=== {__name__} ===")
    print(f"Project: {get_config().get('project_name', 'Unknown')}")
    print(f"Version: {get_config().get('version', 'Unknown')}")
    print()

    # Discover Python files in the project
    root_dir = os.path.dirname(os.path.abspath(__file__))
    py_files = discover_python_files(root_dir)
    print(f"Discovered {len(py_files)} Python file(s):")
    for f in py_files:
        print(f"  - {f}")
    print()

    # Chunk the code files
    if py_files:
        chunks = chunk_code(py_files)
        print(f"Chunked into {len(chunks)} code segment(s).")
        if chunks:
            print(f"Sample chunk: {chunks[0]['id']}")
            print(f"  Lines {chunks[0]['start_line']}-{chunks[0]['end_line']}")
            print(f"  Text preview: {chunks[0]['text'][:80]}...")
        print()

    # Note: Pinecone indexing and query retrieval would be
    # performed through the ADK agent interface
    print("Use 'adk run code_helper' to interact with the AI code assistant.")


if __name__ == "__main__":
    import os
    main()