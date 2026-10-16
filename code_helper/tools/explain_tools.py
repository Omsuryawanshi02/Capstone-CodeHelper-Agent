"""File reading and explanation tools.

Provides read_project_file for safe file reading within the project root,
and supports the Code Explainer agent's Filesystem MCP integration.
"""

import os
from pathlib import Path


def read_project_file(file_path: str) -> str:
    """Safely read a file within the allowed project roots.

    Prevents path traversal, rejects non-.py files, and allows reading
    Python source files from target_project/ and code_helper/ (including agent.py).

    Args:
        file_path: Relative path or filename from the project root to read.

    Returns:
        File contents as a string, or error message if file cannot be read.
    """
    # Resolve the path - normalize and reject absolute paths
    normalized = os.path.normpath(file_path)

    # Reject path traversal attempts and absolute paths
    if (
        normalized.startswith("..")
        or normalized.startswith("/")
        or normalized.startswith("\\")
        or (len(normalized) > 1 and normalized[1] == ":")
    ):
        return f"Error: Path traversal detected or absolute path: {file_path}"

    # Reject if not a .py file (only source code files allowed)
    if not normalized.endswith(".py"):
        return f"Error: Only .py files are allowed, got: {file_path}"

    # Repository root and allowed source directories
    repo_root = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    target_project_dir = os.path.abspath(os.path.join(repo_root, "target_project"))
    code_helper_dir = os.path.abspath(os.path.join(repo_root, "code_helper"))

    candidate_paths = []

    # 1. Path relative to repo root (e.g. "code_helper/agent.py" or "target_project/config.py")
    candidate_paths.append(os.path.normpath(os.path.join(repo_root, normalized)))

    # 2. Path relative to target_project (e.g. "config.py" -> target_project/config.py)
    candidate_paths.append(os.path.normpath(os.path.join(target_project_dir, normalized)))

    # 3. Path relative to code_helper (e.g. "agent.py" -> code_helper/agent.py)
    candidate_paths.append(os.path.normpath(os.path.join(code_helper_dir, normalized)))

    # 4. Special alias for coordinator source file
    if normalized.lower() in ("coordinator.py", "coordinator_agent.py"):
        candidate_paths.append(os.path.normpath(os.path.join(code_helper_dir, "agent.py")))

    resolved_path = None
    for cand in candidate_paths:
        # Strict boundary guard: must be strictly inside target_project_dir or code_helper_dir
        in_target = cand.startswith(target_project_dir + os.sep) or cand == target_project_dir
        in_helper = cand.startswith(code_helper_dir + os.sep) or cand == code_helper_dir
        if (in_target or in_helper) and os.path.isfile(cand):
            resolved_path = cand
            break

    if not resolved_path:
        return f"Error: File not found: {file_path}"

    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            return f.read()
    except PermissionError:
        return f"Error: Permission denied reading: {file_path}"
    except UnicodeDecodeError:
        return f"Error: Cannot decode file (not UTF-8): {file_path}"
    except Exception as e:
        return f"Error reading file {file_path}: {e}"


def explain_code(file_path: str) -> str:
    """Read a Python source file from the project to explain its contents.

    Args:
        file_path: Relative path of the file from the project root (e.g. 'main.py' or 'code_helper/agent.py').

    Returns:
        The content of the file, or an error message if the file cannot be read.
    """
    return read_project_file(file_path)