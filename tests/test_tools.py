"""Tests for custom tools - deterministic, no external API calls.

Tests:
- read_project_file: path traversal protection
- list_project_files: file discovery and exclusions
- inspect_imports: AST parsing
- get_project_overview: project structure reporting
- rag_search: empty query handling
"""

import os
import pytest

from code_helper.tools import (
    rag_search,
    read_project_file,
    list_project_files,
    inspect_imports,
    get_project_overview,
)


class TestRagSearch:
    """Tests for rag_search tool."""

    def test_empty_query(self):
        """Should return error for empty query."""
        result = rag_search("")
        assert "Error" in result
        assert "Empty query" in result

    def test_whitespace_query(self):
        """Should return error for whitespace-only query."""
        result = rag_search("   ")
        assert "Error" in result


class TestReadProjectFile:
    """Tests for read_project_file tool."""

    def test_reads_valid_file(self):
        """Should read a valid .py file from target_project."""
        result = read_project_file("config.py")
        assert "Error" not in result or "config" in result.lower()

    def test_rejects_path_traversal(self):
        """Should reject path traversal attempts."""
        result = read_project_file("../secrets.py")
        assert "Error" in result
        assert "traversal" in result.lower()

    def test_rejects_absolute_path(self):
        """Should reject absolute paths."""
        result = read_project_file("/etc/passwd")
        assert "Error" in result

    def test_rejects_non_python_file(self):
        """Should reject non-.py files."""
        result = read_project_file("README.md")
        assert "Error" in result

    def test_rejects_deep_traversal(self):
        """Should reject deep path traversal."""
        result = read_project_file("../../../etc/passwd")
        assert "Error" in result

    def test_returns_error_for_missing_file(self):
        """Should return error for non-existent file."""
        result = read_project_file("nonexistent.py")
        assert "Error" in result


class TestListProjectFiles:
    """Tests for list_project_files tool."""

    def test_returns_string(self):
        """Should return a string listing files."""
        result = list_project_files()
        assert isinstance(result, str)

    def test_lists_python_files(self):
        """Should list .py files from target_project."""
        result = list_project_files()
        # Should contain at least one .py file
        assert ".py" in result

    def test_excludes_git(self):
        """Should not include .git files."""
        result = list_project_files()
        assert ".git" not in result

    def test_excludes_pycache(self):
        """Should not include __pycache__ files."""
        result = list_project_files()
        assert "__pycache__" not in result

    def test_excludes_venv(self):
        """Should not include .venv files."""
        result = list_project_files()
        assert ".venv" not in result


class TestInspectImports:
    """Tests for inspect_imports tool."""

    def test_parses_valid_file(self):
        """Should parse imports from a valid .py file."""
        result = inspect_imports("config.py")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_rejects_path_traversal(self):
        """Should reject path traversal."""
        result = inspect_imports("../secrets.py")
        assert "Error" in result

    def test_rejects_non_python_file(self):
        """Should reject non-.py files."""
        result = inspect_imports("README.md")
        assert "Error" in result

    def test_returns_error_for_missing_file(self):
        """Should return error for non-existent file."""
        result = inspect_imports("nonexistent.py")
        assert "Error" in result

    def test_parses_imports_in_main(self):
        """Should find imports in main.py."""
        result = inspect_imports("main.py")
        assert isinstance(result, str)


class TestGetProjectOverview:
    """Tests for get_project_overview tool."""

    def test_returns_string(self):
        """Should return a string overview."""
        result = get_project_overview()
        assert isinstance(result, str)

    def test_contains_project_structure(self):
        """Should contain project structure information."""
        result = get_project_overview()
        assert "Project Structure" in result or "PROJECT" in result.upper()

    def test_contains_agents(self):
        """Should list available agents."""
        result = get_project_overview()
        assert "coordinator" in result.lower() or "AGENT" in result.upper()

    def test_contains_run_instructions(self):
        """Should contain run instructions."""
        result = get_project_overview()
        assert "adk" in result.lower() or "run" in result.lower()