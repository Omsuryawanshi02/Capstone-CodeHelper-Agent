"""File reading and explanation tools.

Provides read_project_file for safe file reading within the project root,
and supports the Code Explainer agent's Filesystem MCP integration.
"""

import os
import ast
from pathlib import Path
from typing import Optional, Any, Union


def read_project_file(
    file_path: str, start_line: Any = 1, end_line: Optional[Any] = None
) -> str:
    """Safely read a file within the allowed project roots.

    Prevents path traversal, rejects non-.py files, and allows reading
    Python source files from target_project/ and code_helper/ (including agent.py and rag_pipeline.py).
    Supports optional line range selection via start_line and end_line.

    Args:
        file_path: Relative path or filename from the project root to read.
        start_line: 1-based start line (default: 1).
        end_line: 1-based end line inclusive (default: None, reads to end).

    Returns:
        File contents as a string, or error message if file cannot be read.
    """
    # Safe coercion for line numbers if passed as strings by LLM
    try:
        s_line = int(start_line) if start_line is not None else 1
    except (ValueError, TypeError):
        s_line = 1
    if s_line < 1:
        s_line = 1

    try:
        e_line = int(end_line) if end_line is not None and str(end_line).strip() != "" else None
    except (ValueError, TypeError):
        e_line = None

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

    # 4. Fallback search by filename in case the LLM prefixed the wrong directory
    base_name = os.path.basename(normalized)
    if base_name and base_name != normalized:
        candidate_paths.append(os.path.normpath(os.path.join(code_helper_dir, base_name)))
        candidate_paths.append(os.path.normpath(os.path.join(target_project_dir, base_name)))

    # 5. Special alias for coordinator source file
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
            raw_text = f.read()

        if e_line is not None:
            lines = raw_text.splitlines(keepends=True)
            total = len(lines)
            s_idx = max(0, s_line - 1)
            e_idx = min(total, max(0, e_line))
            return "".join(lines[s_idx:e_idx])

        return raw_text
    except PermissionError:
        return f"Error: Permission denied reading: {file_path}"
    except UnicodeDecodeError:
        return f"Error: Cannot decode file (not UTF-8): {file_path}"
    except Exception as e:
        return f"Error reading file {file_path}: {e}"


def explain_code(file_path: str, max_lines: Any = 120) -> str:
    """Read a Python source file from the project and format it for explanation.

    For compact files (<= 120 lines), formats the code with line numbers.
    For large files (> 120 lines), builds an AST-extracted architectural structural
    summary with function signatures, exact line ranges, and key excerpts to prevent
    GPU VRAM context overflow while providing complete step-by-step structural evidence.

    Args:
        file_path: Relative path of the file from the project root (e.g. 'main.py' or 'code_helper/agent.py').
        max_lines: Line threshold before summarizing large files (default: 120).

    Returns:
        Structured explanation text with line numbers and evidence.
    """
    try:
        limit = int(max_lines) if max_lines is not None and str(max_lines).strip() != "" else 120
    except (ValueError, TypeError):
        limit = 120

    raw_content = read_project_file(file_path)
    if raw_content.startswith("Error:"):
        return raw_content

    lines = raw_content.splitlines(keepends=True)
    total_lines = len(lines)

    # For compact files, return verbatim with 1-based line numbers
    if total_lines <= limit:
        numbered = [f"{i+1:3d}: {line}" for i, line in enumerate(lines)]
        return f"=== File: {file_path} ({total_lines} lines) ===\n" + "".join(numbered)

    # For larger files (> 120 lines), provide AST architectural breakdown to avoid GPU memory overflow
    parts = [
        f"=== File: {file_path} ({total_lines} lines) ===",
        "Architectural Structural Summary with Exact Line Ranges:\n",
    ]

    try:
        tree = ast.parse(raw_content)
        doc = ast.get_docstring(tree)
        if doc:
            parts.append(f"Module Overview:\n{doc.strip()}\n")

        funcs = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", node.lineno)
                fdoc = ast.get_docstring(node) or ""
                fdoc_first = fdoc.strip().split("\n")[0] if fdoc else ""
                arg_list = ", ".join([a.arg for a in node.args.args])
                funcs.append(
                    f"- def {node.name}({arg_list}): lines {node.lineno}-{end} ({fdoc_first})"
                )
            elif isinstance(node, ast.ClassDef):
                end = getattr(node, "end_lineno", node.lineno)
                cdoc = ast.get_docstring(node) or ""
                cdoc_first = cdoc.strip().split("\n")[0] if cdoc else ""
                funcs.append(
                    f"- class {node.name}: lines {node.lineno}-{end} ({cdoc_first})"
                )

        if funcs:
            parts.append("Functions and Components:\n" + "\n".join(funcs) + "\n")
    except Exception as e:
        parts.append(f"Note: AST summary extraction note: {e}\n")

    parts.append("Initial Excerpt (Lines 1-50):")
    excerpt_limit = min(50, total_lines)
    for i in range(excerpt_limit):
        parts.append(f"{i+1:3d}: {lines[i]}")

    parts.append(
        f"\n[Note: This file contains {total_lines} lines across the components cataloged above. All line numbers and signatures are verified via AST analysis.]"
    )
    return "\n".join(parts)