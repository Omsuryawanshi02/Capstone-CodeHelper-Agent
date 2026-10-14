"""Tests for the RAG pipeline - Stage 1 (file ingestion) and Stage 2 (chunking).

These tests run without external API calls - they use only local
filesystem operations and deterministic functions.
"""

import os
import tempfile
import pytest

from code_helper.rag_pipeline import (
    discover_source_files,
    read_source_file,
    chunk_code,
)


class TestDiscoverSourceFiles:
    """Tests for Stage 1: file discovery."""

    def test_discovers_python_files(self, tmp_path):
        """Should find .py files in the directory tree."""
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def add(a, b): return a + b")

        files = discover_source_files(str(tmp_path))
        assert len(files) == 2
        assert any(f.endswith("main.py") for f in files)
        assert any(f.endswith("utils.py") for f in files)

    def test_excludes_git_directory(self, tmp_path):
        """Should not include files from .git directory."""
        (tmp_path / "main.py").write_text("print('hello')")
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config.py").write_text("git config")

        files = discover_source_files(str(tmp_path))
        assert len(files) == 1
        assert all(".git" not in f for f in files)

    def test_excludes_venv_directory(self, tmp_path):
        """Should not include files from .venv directory."""
        (tmp_path / "main.py").write_text("print('hello')")
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "lib.py").write_text("import os")

        files = discover_source_files(str(tmp_path))
        assert len(files) == 1
        assert all(".venv" not in f for f in files)

    def test_excludes_pycache(self, tmp_path):
        """Should not include __pycache__ directories."""
        (tmp_path / "main.py").write_text("print('hello')")
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "main.cpython-314.pyc").write_text("bytecode")

        files = discover_source_files(str(tmp_path))
        assert len(files) == 1

    def test_excludes_non_python_files(self, tmp_path):
        """Should only return .py files."""
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "data.json").write_text("{}")

        files = discover_source_files(str(tmp_path))
        assert len(files) == 1
        assert files[0].endswith(".py")

    def test_returns_sorted_list(self, tmp_path):
        """Should return files in sorted order for determinism."""
        (tmp_path / "zebra.py").write_text("z")
        (tmp_path / "alpha.py").write_text("a")
        (tmp_path / "middle.py").write_text("m")

        files = discover_source_files(str(tmp_path))
        basenames = [os.path.basename(f) for f in files]
        assert basenames == ["alpha.py", "middle.py", "zebra.py"]


class TestReadSourceFile:
    """Tests for reading source files."""

    def test_reads_valid_file(self, tmp_path):
        """Should read a valid UTF-8 file."""
        content = "print('hello world')\n"
        file_path = tmp_path / "test.py"
        file_path.write_text(content, encoding="utf-8")

        result = read_source_file(str(file_path))
        assert result == content

    def test_returns_none_for_missing_file(self, tmp_path):
        """Should return None for non-existent file."""
        result = read_source_file(str(tmp_path / "nonexistent.py"))
        assert result is None

    def test_handles_unicode_decode_error(self, tmp_path):
        """Should return None for non-UTF-8 files."""
        file_path = tmp_path / "binary.py"
        file_path.write_bytes(b"\xff\xfe\x00\x01")

        result = read_source_file(str(file_path))
        assert result is None


class TestChunkCode:
    """Tests for Stage 2: chunking."""

    def test_basic_chunking(self):
        """Should split text into chunks of specified size."""
        text = "\n".join(f"line {i}" for i in range(1, 201))
        chunks = chunk_code("test.py", text, chunk_size=100, overlap=20)

        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk["filename"] == "test.py"
            assert "id" in chunk
            assert "start_line" in chunk
            assert "end_line" in chunk
            assert "text" in chunk

    def test_chunk_line_numbers(self):
        """Should have correct 1-based line numbers."""
        text = "\n".join(f"line {i}" for i in range(1, 101))
        chunks = chunk_code("test.py", text, chunk_size=50, overlap=10)

        assert chunks[0]["start_line"] == 1
        assert chunks[0]["end_line"] == 50

        # Second chunk starts after overlap
        assert chunks[1]["start_line"] == 41

    def test_stable_chunk_ids(self):
        """Should generate stable chunk IDs."""
        text = "line 1\nline 2\nline 3\n"
        chunks1 = chunk_code("test.py", text, chunk_size=2, overlap=0)
        chunks2 = chunk_code("test.py", text, chunk_size=2, overlap=0)

        assert [c["id"] for c in chunks1] == [c["id"] for c in chunks2]

    def test_empty_text(self):
        """Should return empty list for empty text."""
        chunks = chunk_code("test.py", "")
        assert chunks == []

    def test_single_chunk(self):
        """Should return single chunk for short text."""
        text = "short text"
        chunks = chunk_code("test.py", text, chunk_size=100, overlap=20)
        assert len(chunks) == 1
        assert chunks[0]["start_line"] == 1

    def test_prevents_empty_chunks(self):
        """Should not create chunks with only whitespace."""
        text = "line 1\n\n\n\nline 5\n"
        chunks = chunk_code("test.py", text, chunk_size=2, overlap=0)
        for chunk in chunks:
            assert chunk["text"].strip() != ""

    def test_invalid_chunk_size(self):
        """Should raise ValueError for invalid chunk size."""
        with pytest.raises(ValueError):
            chunk_code("test.py", "text", chunk_size=0, overlap=0)

    def test_invalid_overlap(self):
        """Should raise ValueError when overlap >= chunk_size."""
        with pytest.raises(ValueError):
            chunk_code("test.py", "text", chunk_size=10, overlap=10)

    def test_negative_overlap(self):
        """Should raise ValueError for negative overlap."""
        with pytest.raises(ValueError):
            chunk_code("test.py", "text", chunk_size=10, overlap=-1)

    def test_chunk_overlap_works(self):
        """Should have overlapping lines between consecutive chunks."""
        text = "\n".join(f"line {i}" for i in range(1, 101))
        chunks = chunk_code("test.py", text, chunk_size=30, overlap=10)

        assert len(chunks) >= 3
        # Check overlap: last lines of chunk 0 appear in chunk 1
        chunk0_lines = chunks[0]["text"].splitlines()
        chunk1_lines = chunks[1]["text"].splitlines()

        # Last 10 lines of chunk 0 should equal first 10 lines of chunk 1
        assert chunk0_lines[-10:] == chunk1_lines[:10]

    def test_preserves_original_text(self):
        """Should preserve original source text in chunks."""
        text = "def foo():\n    return 42\n"
        chunks = chunk_code("test.py", text, chunk_size=100, overlap=20)

        assert chunks[0]["text"] == text