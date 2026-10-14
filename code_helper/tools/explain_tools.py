"""File reading and explanation tools.

Provides read_project_file for safe file reading within the project root,
and supports the Code Explainer agent's Filesystem MCP integration.
"""

import os
from pathlib import Path


def read_project_file(file_path: str) -> str:
    """Safely read a file within the allowed project root.

    Prevents path traversal and rejects unauthorized files.

    Args:
        file_path: Relative path from the project root to read.

    Returns:
        File contents as a string, or error message if file cannot be read.
    """
    # Resolve the path - normalize and reject absolute paths
    normalized = os.path.normpath(file_path)

    # Reject path traversal attempts
    if normalized.startswith("..") or normalized.startswith("/"):
        return f"Error: Path traversal detected or absolute path: {file_path}"

    # Build the absolute path relative to the project root
    # The target project is at ../../target_project/ relative to code_helper/tools/
    project_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "target_project",
    )
    absolute_path = os.path.normpath(os.path.join(project_root, normalized))

    # Additional safety: ensure the resolved path is within the target project
    if not absolute_path.startswith(os.path.normpath(project_root) + os.sep) and \
       absolute_path != os.path.normpath(project_root):
        return f"Error: File outside allowed project root: {file_path}"

    # Reject if not a .py file (only source code files allowed)
    if not normalized.endswith(".py"):
        return f"Error: Only .py files are allowed, got: {file_path}"

    try:
        with open(absolute_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except PermissionError:
        return f"Error: Permission denied reading: {file_path}"
    except UnicodeDecodeError:
        return f"Error: Cannot decode file (not UTF-8): {file_path}"
    except Exception as e:
        return f"Error reading file {file_path}: {e}"