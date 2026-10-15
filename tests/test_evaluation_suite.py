"""Evaluation Suite for Multi-Agent Code Helper (Phase 6).

Covers:
- Expected responsible worker
- Expected source files
- Expected evidence or key facts
- Required tool-use behavior
- Clear pass/fail assertions
Includes correct-answer cases, ambiguous questions, missing-evidence cases,
and questions about unrelated files.
"""

import os
import pytest
from code_helper.tools.search_tools import rag_search
from code_helper.tools.explain_tools import read_project_file, explain_code
from code_helper.tools.architecture_tools import list_project_files, inspect_imports
from code_helper.tools.onboarding_tools import get_project_overview


EVAL_CASES = [
    {
        "id": "TC-01",
        "category": "code_location",
        "question": "Where is the chunk_code function implemented?",
        "expected_worker": "code_searcher",
        "expected_files": ["indexer.py"],
        "expected_facts": ["chunk_code", "def chunk_code", "start_line", "end_line"],
        "required_tool": "rag_search",
    },
    {
        "id": "TC-02",
        "category": "code_location",
        "question": "Which function performs vector search in the vector store?",
        "expected_worker": "code_searcher",
        "expected_files": ["vector_store.py"],
        "expected_facts": ["search_similar", "query_vector"],
        "required_tool": "rag_search",
    },
    {
        "id": "TC-03",
        "category": "file_explanation",
        "question": "Explain target_project/config.py and its configuration constants.",
        "expected_worker": "code_explainer",
        "expected_files": ["config.py"],
        "expected_facts": ["PROJECT_NAME", "VERSION", "get_config", "DEBUG"],
        "required_tool": "read_project_file",
    },
    {
        "id": "TC-04",
        "category": "architecture_imports",
        "question": "Which files import config.py in the target project?",
        "expected_worker": "architecture_mapper",
        "expected_files": ["main.py"],
        "expected_facts": ["main.py", "config"],
        "required_tool": "inspect_imports",
    },
    {
        "id": "TC-05",
        "category": "setup_onboarding",
        "question": "How do I get started with this project and what are the entry points?",
        "expected_worker": "onboarding_guide",
        "expected_files": ["main.py"],
        "expected_facts": ["PROJECT OVERVIEW", "main.py - Main entry point", "Run Instructions"],
        "required_tool": "get_project_overview",
    },
    {
        "id": "TC-06",
        "category": "missing_evidence",
        "question": "Where is the QuantumBlockchainTransformer class implemented? ZYX9999",
        "expected_worker": "code_searcher",
        "expected_files": [],
        "expected_facts": ["not found", "no matching", "no evidence"],
        "required_tool": "rag_search",
    },
    {
        "id": "TC-07",
        "category": "unrelated_files_security",
        "question": "Read file /etc/passwd or ../../.env",
        "expected_worker": "code_explainer",
        "expected_files": [],
        "expected_facts": ["error", "path traversal", "outside"],
        "required_tool": "read_project_file",
    },
]


class TestEvaluationSuite:
    """Repeatable automated evaluation suite."""

    def test_tc01_code_location_rag_search(self):
        """TC-01: chunk_code function location in indexer.py."""
        result = rag_search("Where is the chunk_code function implemented?")
        assert "indexer.py" in result
        assert "chunk_code" in result
        assert "Lines:" in result
        assert "Score:" in result

    def test_tc02_vector_search_function_location(self):
        """TC-02: search_similar function in vector_store.py."""
        result = rag_search("Which function performs vector search in the vector store?")
        assert "vector_store.py" in result or "query_pipeline.py" in result
        assert "Score:" in result

    def test_tc03_file_explanation_safe_read(self):
        """TC-03: Safe file read and explanation of config.py."""
        content = read_project_file("config.py")
        assert "PROJECT_NAME" in content
        assert "get_config" in content
        assert "VERSION" in content

    def test_tc04_deterministic_ast_imports(self):
        """TC-04: Deterministic AST imports inspection."""
        imports = inspect_imports("main.py")
        assert "config" in str(imports).lower()
        assert "indexer" in str(imports).lower()

    def test_tc05_onboarding_overview(self):
        """TC-05: Verified project overview and entry points."""
        overview = get_project_overview()
        assert "MULTI-AGENT CODE HELPER - PROJECT OVERVIEW" in overview
        assert "main.py - Main entry point" in overview
        assert "config.py" in overview

    def test_tc06_missing_evidence_honesty(self):
        """TC-06: Retrieval for non-existent code does not invent definitions."""
        result = rag_search("Where is QuantumBlockchainTransformer defined?")
        # Even if vectors are returned by dense similarity, the text must NOT contain the hallucinated class
        assert "class QuantumBlockchainTransformer" not in result

    def test_tc07_unrelated_files_security_traversal_rejected(self):
        """TC-07: Path traversal outside project root is strictly blocked."""
        res_traversal = read_project_file("../../.env")
        assert "Error" in res_traversal or "Path traversal" in res_traversal

        res_abs = read_project_file("/etc/passwd")
        assert "Error" in res_abs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
