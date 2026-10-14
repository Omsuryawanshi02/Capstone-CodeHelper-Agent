"""CLI entry point for indexing a codebase.

Run:
    python -m code_helper.index_codebase

Indexes the target project files into Pinecone using the
custom RAG pipeline (no LangChain, no LlamaIndex).
"""

import argparse
import logging
import os
import sys

from .rag_pipeline import index_project
from .config import validate_config


def main():
    parser = argparse.ArgumentParser(
        description="Index a Python codebase into Pinecone for RAG retrieval."
    )
    parser.add_argument(
        "--project",
        default=None,
        help="Path to the target project directory (default: target_project/)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    # Determine project directory
    if args.project:
        project_dir = args.project
    else:
        # Default to target_project relative to package root
        package_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.join(os.path.dirname(package_dir), "target_project")

    if not os.path.isdir(project_dir):
        print(f"Error: Project directory not found: {project_dir}")
        sys.exit(1)

    if not validate_config():
        print("Error: Missing required environment variables.")
        print("Required: NVIDIA_NIM_API_KEY, PINECONE_API_KEY")
        sys.exit(1)

    print(f"Indexing project: {project_dir}")
    print("-" * 50)

    stats = index_project(project_dir)

    print(f"Files discovered:  {stats['files_discovered']}")
    print(f"Files read:        {stats['files_read']}")
    print(f"Chunks created:    {stats['chunks_created']}")
    print(f"Vectors upserted:  {stats['vectors_upserted']}")

    if stats["errors"]:
        print("\nErrors:")
        for error in stats["errors"]:
            print(f"  - {error}")
    else:
        print("\nIndexing completed successfully.")


if __name__ == "__main__":
    main()