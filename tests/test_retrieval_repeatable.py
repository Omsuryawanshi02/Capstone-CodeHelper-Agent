"""Repeatable test script for Phase 2 — Test retrieval separately.

Tests rag_search directly across the 5 required benchmark questions:
1. Where is the Pinecone index configured?
2. Which files import config.py?
3. What does query_pipeline.py do?
4. Which function performs vector retrieval?
5. What happens when the repository contains no relevant evidence?
"""

import json
import pytest
from code_helper.tools.search_tools import rag_search


BENCHMARK_QUERIES = [
    {
        "id": 1,
        "question": "Where is the Pinecone index configured?",
        "expected_files": ["vector_store.py", "query_pipeline.py", "config.py"],
        "expected_facts": ["index", "Pinecone", "vector"],
    },
    {
        "id": 2,
        "question": "Which files import config.py?",
        "expected_files": ["main.py", "config.py"],
        "expected_facts": ["config", "import"],
    },
    {
        "id": 3,
        "question": "What does query_pipeline.py do?",
        "expected_files": ["query_pipeline.py"],
        "expected_facts": ["query", "pipeline", "retrieve_relevant_chunks"],
    },
    {
        "id": 4,
        "question": "Which function performs vector retrieval?",
        "expected_files": ["vector_store.py", "query_pipeline.py"],
        "expected_facts": ["search_similar", "retrieve_relevant_chunks", "query"],
    },
    {
        "id": 5,
        "question": "What happens when the repository contains no relevant evidence? ZYXWVU12345NonExistentToken",
        "expected_files": [],
        "expected_facts": [],
    },
]


def run_single_query(q_item):
    question = q_item["question"]
    raw_output = rag_search(question)

    chunks = []
    # Parse formatted output lines:
    # Score: 0.7546 | File: query_pipeline.py | Lines: 1-87
    lines = raw_output.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("Score:"):
            parts = [p.strip() for p in line.split("|")]
            score_str = parts[0].replace("Score:", "").strip()
            file_str = parts[1].replace("File:", "").strip()
            lines_str = parts[2].replace("Lines:", "").strip()
            snippet = lines[i+1].strip() if i+1 < len(lines) else ""
            chunks.append({
                "score": float(score_str),
                "filename": file_str,
                "lines": lines_str,
                "snippet": snippet,
            })
            i += 2
        else:
            i += 1

    return {
        "question": question,
        "raw_output": raw_output,
        "retrieved_count": len(chunks),
        "chunks": chunks,
    }


def test_repeatable_retrieval_benchmarks():
    results = []
    for item in BENCHMARK_QUERIES:
        res = run_single_query(item)
        results.append(res)
        assert not res["raw_output"].startswith("Error")
        assert res["retrieved_count"] > 0


if __name__ == "__main__":
    for item in BENCHMARK_QUERIES:
        res = run_single_query(item)
        print(f"\n=== Q{item['id']}: {item['question']} ===")
        print(f"Raw Output Status: {'OK' if not res['raw_output'].startswith('Error') else 'ERROR'}")
        print(f"Chunks Retrieved: {res['retrieved_count']}")
        for c in res["chunks"]:
            print(f"  Score: {c['score']:.4f} | File: {c['filename']} | Lines: {c['lines']}")
