"""Indexer module for the target Python project.

Responsible for scanning source files, extracting metadata,
 and preparing code chunks for the RAG pipeline ingestion stage.
"""

import os
from pathlib import Path
from ..config import CHUNK_SIZE, CHUNK_OVERLAP


def discover_python_files(root_dir: str) -> list:
    """Discover all .py files in the target project, excluding irrelevant content.

    Args:
        root_dir: Root directory to search for Python files.

    Returns:
        List of relative file paths for .py files.
    """
    excluded = {".git", ".venv", "__pycache__", ".pytest_cache"}
    py_files = []

    for root, dirs, files in os.walk(root_dir):
        # Exclude unwanted directories
        dirs[:] = [d for d in dirs if d not in excluded]

        for f in files:
            if f.endswith(".py"):
                full_path = Path(root) / f
                # Get path relative to root_dir
                rel_path = full_path.relative_to(root_dir)
                py_files.append(str(rel_path))

    return sorted(py_files)


def chunk_code(files: list, chunk_size: int = None, overlap: int = None) -> list:
    """Split Python source files into code chunks for RAG embedding.

    Each chunk includes:
    - Stable chunk ID
    - Relative filename
    - Start line (1-based)
    - End line (1-based)
    - Original text

    Uses line-based chunking with configurable size and overlap.
    Note: Line-based chunking may split function definitions,
    so boundary adjustments are recommended for production use.

    Args:
        files: List of relative file paths to chunk.
        chunk_size: Number of lines per chunk (default: CHUNK_SIZE from config).
        overlap: Number of overlap lines between chunks (default: CHUNK_OVERLAP from config).

    Returns:
        List of chunk dictionaries with keys: id, filename, start_line, end_line, text.
    """
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if overlap is None:
        overlap = CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("Overlap must be less than chunk size.")

    chunks = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            continue

        total_lines = len(lines)
        if total_lines == 0:
            continue

        chunk_id = 0
        start = 0

        while start < total_lines:
            end = min(start + chunk_size, total_lines)
            chunk_lines = lines[start:end]
            chunk_text = "".join(chunk_lines)

            # Generate stable chunk ID
            chunk_id_str = f"{file_path}:{start + 1}-{end}"

            chunks.append({
                "id": chunk_id_str,
                "filename": str(file_path),
                "start_line": start + 1,  # 1-based
                "end_line": end,  # 1-based (inclusive)
                "text": chunk_text,
            })

            start += chunk_size - overlap

        # Remove duplicate consecutive chunks with identical text
        seen = set()
        unique_chunks = []
        for c in chunks:
            key = c["text"][:50] if c["text"] else ""
            if key not in seen:
                seen.add(key)
                unique_chunks.append(c)

    return unique_chunks


def get_file_summary(file_path: str) -> str:
    """Return a brief summary of a Python file's contents.

    Args:
        file_path: Relative path to the file.

    Returns:
        String describing the file's purpose based on its first few lines
        and top-level definitions.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return f"Could not read {file_path}"

    # Take first 20 lines for summary
    summary_lines = lines[:20]
    summary = "".join(summary_lines)

    # Look for top-level defs/class
    import re
    defs = re.findall(r"^def (\w+)|^class (\w+)", summary, re.MULTILINE)
    names = [name for pair in defs for name in pair if name]

    if names:
        return f"{os.path.basename(file_path)}: contains {', '.join(names[:3])}"
    else:
        return f"{os.path.basename(file_path)}: {summary[:100].strip()}"