import { CodeFileNode, ArchitectureData, ChangeReviewReport, ChatMessage } from '../types';

export const TARGET_PROJECT_FILES: CodeFileNode[] = [
  {
    path: 'target_project/config.py',
    name: 'config.py',
    extension: 'py',
    sizeBytes: 923,
    lineCount: 37,
    functionsCount: 1,
    classesCount: 0,
    imports: ['os', 'dotenv.load_dotenv'],
    docstring: 'Configuration module for the target Python project. Global configuration settings and environment variable loading.',
    astValid: true,
    content: `"""Configuration module for the target Python project.

Contains global configuration settings, constants, and environment
variable loading logic for the codebase.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project constants
PROJECT_NAME = "Sample Python Project"
VERSION = "1.0.0"

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", "8080"))

# Feature flags
FEATURE_A = os.getenv("FEATURE_A", "False").lower() == "true"
FEATURE_B = os.getenv("FEATURE_B", "False").lower() == "true"


def get_config():
    """Return a configuration dictionary."""
    return {
        "project_name": PROJECT_NAME,
        "version": VERSION,
        "debug": DEBUG,
        "host": HOST,
        "port": PORT,
        "feature_a": FEATURE_A,
        "feature_b": FEATURE_B,
    }`
  },
  {
    path: 'target_project/query_pipeline.py',
    name: 'query_pipeline.py',
    extension: 'py',
    sizeBytes: 2695,
    lineCount: 87,
    functionsCount: 2,
    classesCount: 0,
    imports: ['..config.NVIDIA_EMBED_MODEL', '..config.validate_config', 'litellm.embedding'],
    docstring: 'Coordinates RAG pipeline stages: embedding with NVIDIA NIM, vector retrieval in Pinecone, and formatting chunk results.',
    astValid: true,
    content: `"""Query pipeline module for the target Python project.

Coordinates the RAG pipeline stages: retrieval, formatting,
and response generation for user queries about the codebase.

Wires together embedding, vector storage (Pinecone), and retrieval
to answer developer questions.
"""

from ..config import NVIDIA_EMBED_MODEL, validate_config


def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list:
    """Retrieve the top-k most relevant code chunks for a natural-language query.

    Stage 5 of the RAG pipeline: embed the query and retrieve matching chunks
    from Pinecone.

    Args:
        query: Natural-language question about the codebase.
        top_k: Number of top matches to retrieve (default: 5).

    Returns:
        List of dicts with keys: filename, start_line, end_line, score, text.
        Returns empty list if no matches found or configuration is missing.
    """
    if not query or not query.strip():
        return []

    if not validate_config():
        return []

    try:
        from litellm import embedding

        # Embed the query using the same model as documents
        embed_result = embedding(
            model=f"nvidia_nim/{NVIDIA_EMBED_MODEL}",
            input=query,
        )

        if not embed_result or not embed_result.data:
            return []

        query_embedding = embed_result.data[0].embedding

        # Pinecone vector similarity query
        # matches = pinecone_index.query(vector=query_embedding, top_k=top_k, ...)
        return []

    except ImportError:
        return []
    except Exception as e:
        print(f"Error in retrieval: {e}")
        return []


def format_chunk_results(matches: list) -> str:
    """Format search results into a human-readable string.

    Args:
        matches: List of match dicts from Pinecone search.

    Returns:
        Formatted string with filenames, line ranges, scores, and text.
    """
    if not matches:
        return "No matching code chunks found."

    output_lines = []
    for i, match in enumerate(matches, 1):
        score = match.get("score", 0.0)
        metadata = match.get("metadata", {})
        filename = metadata.get("filename", "unknown")
        start_line = metadata.get("start_line", "?")
        end_line = metadata.get("end_line", "?")
        text = metadata.get("text", "")[:200]

        output_lines.append(
            f"{i}. File: {filename} | Lines: {start_line}-{end_line} | "
            f"Score: {score:.4f}\\n   {text}..."
        )

    return "\\n".join(output_lines)`
  },
  {
    path: 'target_project/indexer.py',
    name: 'indexer.py',
    extension: 'py',
    sizeBytes: 4280,
    lineCount: 142,
    functionsCount: 3,
    classesCount: 0,
    imports: ['os', 'pathlib.Path', '..config.CHUNK_SIZE', '..config.CHUNK_OVERLAP'],
    docstring: 'Responsible for scanning source files, extracting metadata, and preparing code chunks for RAG embedding.',
    astValid: true,
    content: `"""Indexer module for the target Python project.

Responsible for scanning source files, extracting metadata,
and preparing code chunks for the RAG pipeline ingestion stage.
"""

import os
from pathlib import Path
from ..config import CHUNK_SIZE, CHUNK_OVERLAP


def discover_python_files(root_dir: str) -> list:
    """Discover all .py files in the target project, excluding irrelevant content."""
    excluded = {".git", ".venv", "__pycache__", ".pytest_cache"}
    py_files = []

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in excluded]

        for f in files:
            if f.endswith(".py"):
                full_path = Path(root) / f
                rel_path = full_path.relative_to(root_dir)
                py_files.append(str(rel_path))

    return sorted(py_files)


def chunk_code(files: list, chunk_size: int = None, overlap: int = None) -> list:
    """Split Python source files into code chunks for RAG embedding."""
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if overlap is None:
        overlap = CHUNK_OVERLAP

    chunks = []
    for file_path in files:
        if not os.path.exists(file_path):
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        start = 0
        while start < len(lines):
            end = min(start + chunk_size, len(lines))
            chunk_text = "".join(lines[start:end])
            chunk_id = f"{file_path}:{start+1}-{end}"
            chunks.append({
                "id": chunk_id,
                "filename": file_path,
                "start_line": start + 1,
                "end_line": end,
                "text": chunk_text,
            })
            if end >= len(lines):
                break
            start += chunk_size - overlap

    return chunks`
  },
  {
    path: 'target_project/vector_store.py',
    name: 'vector_store.py',
    extension: 'py',
    sizeBytes: 2821,
    lineCount: 88,
    functionsCount: 3,
    classesCount: 0,
    imports: ['uuid', 'typing.List', 'typing.Dict', 'typing.Any'],
    docstring: 'Handles storage of code embeddings in Pinecone serverless index with deterministic ID generation.',
    astValid: true,
    content: `"""Vector store module for the target Python project.

Handles storage of code embeddings in Pinecone serverless index.
Provides deterministic ID generation and predictable upsert behavior.
"""

import uuid
from typing import List, Dict, Any


def generate_vector_id(filename: str, start_line: int, end_line: int) -> str:
    """Generate a deterministic vector ID from chunk metadata."""
    hash_input = f"{filename}:{start_line}:{end_line}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hash_input))


def upsert_vectors(index, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Upsert vectors into the Pinecone index with batched requests."""
    if not vectors:
        return {"upserted_count": 0}

    batch_size = 100
    results = []

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        try:
            response = index.upsert(vectors=batch)
            results.append(response)
        except Exception as e:
            print(f"Error upserting batch: {e}")
            results.append({"upserted_count": 0})

    total_upserted = sum(r.get("upserted_count", 0) for r in results)
    return {"upserted_count": total_upserted, "detail": "Batched upsert completed"}


def search_similar(index, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for similar vectors in the Pinecone index."""
    try:
        response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            include_values=False,
        )
        return response.get("matches", [])
    except Exception as e:
        print(f"Error searching Pinecone: {e}")
        return []`
  },
  {
    path: 'target_project/main.py',
    name: 'main.py',
    extension: 'py',
    sizeBytes: 1683,
    lineCount: 53,
    functionsCount: 1,
    classesCount: 0,
    imports: [
      'sys',
      '.config.get_config',
      '.indexer.discover_python_files',
      '.indexer.chunk_code',
      '.vector_store.generate_vector_id',
      '.vector_store.upsert_vectors',
      '.vector_store.search_similar',
      '.query_pipeline.retrieve_relevant_chunks',
      '.query_pipeline.format_chunk_results',
    ],
    docstring: 'Main entry point for target Python project. Demonstrates configuration, indexing, and query capabilities.',
    astValid: true,
    content: `"""Main entry point for the target Python project.

Demonstrates a typical Python project structure with configuration,
indexing, and query capabilities.
"""

import os
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

    root_dir = os.path.dirname(os.path.abspath(__file__))
    py_files = discover_python_files(root_dir)
    print(f"Discovered {len(py_files)} Python file(s):")
    for f in py_files:
        print(f"  - {f}")

    if py_files:
        chunks = chunk_code(py_files)
        print(f"Chunked into {len(chunks)} code segment(s).")

    print("Use 'adk run code_helper' to interact with the AI code assistant.")


if __name__ == "__main__":
    main()`
  }
];

export const ARCHITECTURE_DATA: ArchitectureData = {
  engine: 'deterministic-python-ast',
  llmUsed: false,
  drawioUrl:
    'https://app.diagrams.net/?grid=0&pv=0&border=10&edit=_blank#create=%7B%22type%22%3A%22mermaid%22%2C%22compressed%22%3Atrue%2C%22data%22%3A%22Sy9KLMhQNTIIcVE1cATSQJScn5eWma5q6qRqZARlGxloQFh6BZWaQGFVU4TyzLyU1IrUIoh6GAeoAcrEoiM3MTMPohzMAqoF0VgUFpamFlXGF2QWpOZk5qVCtKCJATWjimAxpiw1uSS%2FKL4YSEANQREBGoHMx%2BNFIwNdXVVjV0QYofiIWFmYaTik0TyIQxWKD3CEF7qDAA%3D%3D%22%2C%22version%22%3A%2212%22%7D',
  mermaidCode: `graph TD
  config["config (config.py)"]
  indexer["indexer (indexer.py)"]
  main["main (main.py)"]
  query_pipeline["query_pipeline (query_pipeline.py)"]
  vector_store["vector_store (vector_store.py)"]
  indexer --> config
  main --> config
  main --> indexer
  main --> query_pipeline
  main --> vector_store
  query_pipeline --> config`,
  modules: [
    {
      id: 'main',
      name: 'main',
      path: 'target_project/main.py',
      lineCount: 53,
      astSymbols: ['main()'],
      incomingImports: [],
      outgoingImports: ['config', 'indexer', 'vector_store', 'query_pipeline'],
      docstring: 'Application entry point orchestration module',
      x: 350,
      y: 60,
    },
    {
      id: 'config',
      name: 'config',
      path: 'target_project/config.py',
      lineCount: 37,
      astSymbols: ['get_config()', 'PROJECT_NAME', 'VERSION', 'DEBUG', 'HOST', 'PORT'],
      incomingImports: ['main', 'indexer', 'query_pipeline'],
      outgoingImports: [],
      docstring: 'Global settings, environment loading, and flags',
      x: 350,
      y: 280,
    },
    {
      id: 'indexer',
      name: 'indexer',
      path: 'target_project/indexer.py',
      lineCount: 142,
      astSymbols: ['discover_python_files()', 'chunk_code()'],
      incomingImports: ['main'],
      outgoingImports: ['config'],
      docstring: 'Source scanning and chunking for ingestion',
      x: 120,
      y: 170,
    },
    {
      id: 'query_pipeline',
      name: 'query_pipeline',
      path: 'target_project/query_pipeline.py',
      lineCount: 87,
      astSymbols: ['retrieve_relevant_chunks()', 'format_chunk_results()'],
      incomingImports: ['main'],
      outgoingImports: ['config'],
      docstring: 'RAG retrieval coordination and result formatting',
      x: 580,
      y: 170,
    },
    {
      id: 'vector_store',
      name: 'vector_store',
      path: 'target_project/vector_store.py',
      lineCount: 88,
      astSymbols: ['generate_vector_id()', 'upsert_vectors()', 'search_similar()'],
      incomingImports: ['main'],
      outgoingImports: [],
      docstring: 'Pinecone vector storage and deterministic ID hashing',
      x: 350,
      y: 170,
    },
  ],
  edges: [
    { source: 'main', target: 'indexer', label: 'imports chunk_code' },
    { source: 'main', target: 'vector_store', label: 'imports upsert_vectors' },
    { source: 'main', target: 'query_pipeline', label: 'imports retrieve_relevant_chunks' },
    { source: 'main', target: 'config', label: 'imports get_config' },
    { source: 'indexer', target: 'config', label: 'imports CHUNK_SIZE' },
    { source: 'query_pipeline', target: 'config', label: 'imports NVIDIA_EMBED_MODEL' },
  ],
};

export const CHANGE_REVIEW_DATA: ChangeReviewReport = {
  branch: 'main',
  baseCommit: 'a89c42f',
  targetCommit: 'HEAD (working tree)',
  riskLevel: 'Medium',
  confidence: 'Confirmed',
  riskExplanation:
    'Modified get_config() signature in config.py and added optional strict=False parameter. While backwards-compatible for standard calls, 2 downstream callers (indexer.py, query_pipeline.py) import config constants directly.',
  recommendedTests: [
    'pytest tests/test_architecture_mapper_no_llm.py -v',
    'pytest tests/test_tools.py -k "test_config" -v',
    'python -m py_compile target_project/config.py target_project/vector_store.py',
  ],
  downstreamImpacts: [
    {
      sourceFile: 'target_project/config.py',
      affectedCallers: ['target_project/indexer.py', 'target_project/query_pipeline.py', 'target_project/main.py'],
    },
    {
      sourceFile: 'target_project/vector_store.py',
      affectedCallers: ['target_project/main.py'],
    },
  ],
  changedFiles: [
    {
      path: 'target_project/config.py',
      status: 'modified',
      isStaged: true,
      additions: 14,
      deletions: 2,
      astDifferences: {
        addedFunctions: ['get_cache_ttl()'],
        modifiedFunctions: ['get_config(env_path, strict=False)'],
        removedFunctions: [],
        addedClasses: [],
        modifiedClasses: [],
      },
      diffLines: [
        { type: 'context', oldLineNumber: 23, newLineNumber: 23, text: ' FEATURE_A = os.getenv("FEATURE_A", "False").lower() == "true"' },
        { type: 'context', oldLineNumber: 24, newLineNumber: 24, text: ' FEATURE_B = os.getenv("FEATURE_B", "False").lower() == "true"' },
        { type: 'context', oldLineNumber: 25, newLineNumber: 25, text: '' },
        { type: 'add', newLineNumber: 26, text: '+CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))' },
        { type: 'add', newLineNumber: 27, text: '+' },
        { type: 'add', newLineNumber: 28, text: '+def get_cache_ttl() -> int:' },
        { type: 'add', newLineNumber: 29, text: '+    """Return cache time-to-live in seconds."""' },
        { type: 'add', newLineNumber: 30, text: '+    return CACHE_TTL_SECONDS' },
        { type: 'add', newLineNumber: 31, text: '+' },
        { type: 'delete', oldLineNumber: 27, text: '-def get_config():' },
        { type: 'add', newLineNumber: 32, text: '+def get_config(env_path: str = None, strict: bool = False) -> dict:' },
        { type: 'context', oldLineNumber: 28, newLineNumber: 33, text: '     """Return a configuration dictionary."""' },
        { type: 'add', newLineNumber: 34, text: '+    if env_path and os.path.exists(env_path):' },
        { type: 'add', newLineNumber: 35, text: '+        load_dotenv(env_path, override=True)' },
        { type: 'context', oldLineNumber: 29, newLineNumber: 36, text: '     return {' },
      ],
    },
    {
      path: 'target_project/vector_store.py',
      status: 'modified',
      isStaged: false,
      additions: 8,
      deletions: 1,
      astDifferences: {
        addedFunctions: ['batch_delete_vectors()'],
        modifiedFunctions: ['upsert_vectors()'],
        removedFunctions: [],
        addedClasses: [],
        modifiedClasses: [],
      },
      diffLines: [
        { type: 'context', oldLineNumber: 47, newLineNumber: 47, text: '     if not vectors:' },
        { type: 'context', oldLineNumber: 48, newLineNumber: 48, text: '         return {"upserted_count": 0}' },
        { type: 'delete', oldLineNumber: 49, text: '-    batch_size = 100' },
        { type: 'add', newLineNumber: 49, text: '+    batch_size = max(10, min(len(vectors), 250)) # dynamic batching' },
        { type: 'context', oldLineNumber: 50, newLineNumber: 50, text: '     results = []' },
        { type: 'add', newLineNumber: 66, text: '+' },
        { type: 'add', newLineNumber: 67, text: '+def batch_delete_vectors(index, ids: List[str]) -> bool:' },
        { type: 'add', newLineNumber: 68, text: '+    """Delete vector batch by deterministic IDs."""' },
        { type: 'add', newLineNumber: 69, text: '+    if not ids: return True' },
        { type: 'add', newLineNumber: 70, text: '+    return index.delete(ids=ids) is not None' },
      ],
    },
    {
      path: 'target_project/cache.py',
      status: 'untracked',
      isStaged: false,
      additions: 22,
      deletions: 0,
      astDifferences: {
        addedFunctions: ['init_memory_cache()', 'get_cached_item()', 'set_cached_item()'],
        modifiedFunctions: [],
        removedFunctions: [],
        addedClasses: ['MemoryCache'],
        modifiedClasses: [],
      },
      diffLines: [
        { type: 'add', newLineNumber: 1, text: '+"""In-memory cache layer for target_project."""' },
        { type: 'add', newLineNumber: 2, text: '+import time' },
        { type: 'add', newLineNumber: 3, text: '+from typing import Dict, Any, Optional' },
        { type: 'add', newLineNumber: 4, text: '+' },
        { type: 'add', newLineNumber: 5, text: '+class MemoryCache:' },
        { type: 'add', newLineNumber: 6, text: '+    def __init__(self, default_ttl: int = 3600):' },
        { type: 'add', newLineNumber: 7, text: '+        self._store: Dict[str, Any] = {}' },
        { type: 'add', newLineNumber: 8, text: '+        self._ttl = default_ttl' },
      ],
    },
  ],
};

export const DEMO_MESSAGES: ChatMessage[] = [
  {
    id: 'demo-msg-1',
    role: 'user',
    content: 'How does the query pipeline retrieve relevant code chunks from Pinecone, and what embedding model does it use?',
    timestamp: Date.now() - 1000 * 60 * 12,
  },
  {
    id: 'demo-msg-2',
    role: 'assistant',
    agentName: 'code_searcher',
    activity: 'Retrieved 2 code chunks via Pinecone vector index and validated NVIDIA NIM embedding configuration',
    timestamp: Date.now() - 1000 * 60 * 11,
    content: `### Query Retrieval Pipeline & Embedding Configuration

The query pipeline retrieves codebase chunks using a **two-step embedding and vector similarity workflow** located in \`target_project/query_pipeline.py\`:

1. **Embedding Stage**: The incoming natural language question is converted into dense vector embeddings using **NVIDIA NIM** via LiteLLM:
   \`model="nvidia_nim/{NVIDIA_EMBED_MODEL}"\` (configured by default to \`nvidia/nemotron-3-embed-1b\`).
2. **Pinecone Vector Search**: The resulting embedding vector is matched against existing code chunks using cosine similarity in the Pinecone serverless index.
3. **Deterministic ID Binding**: Returned matches correspond to deterministic chunk IDs formatted as \`{filename}:{start_line}:{end_line}\` generated in \`target_project/vector_store.py\`.`,
    structuredAnswer: {
      conclusion: 'The query pipeline embeds user queries via NVIDIA NIM (nvidia/nemotron-3-embed-1b) and queries Pinecone for the top-k chunks with deterministic line-bound coordinates.',
      explanation: 'Lines 13-59 in target_project/query_pipeline.py define retrieve_relevant_chunks(). It validates the configuration first, invokes LiteLLM embedding against NVIDIA NIM, and prepares the Pinecone vector query.',
      confidence: 'Confirmed',
      limitations: 'If PINECONE_API_KEY is unset or validate_config() returns False, retrieve_relevant_chunks() safely returns an empty list without raising unhandled exceptions.',
      nextActions: [
        'Inspect vector_store.py to review batch upsert and UUIDv5 hash generation',
        'Run test_architecture_mapper_no_llm.py to verify dependency isolation',
        'View the module dependency diagram for query_pipeline.py',
      ],
    },
    sources: [
      {
        filePath: 'target_project/query_pipeline.py',
        startLine: 13,
        endLine: 59,
        score: 0.94,
        type: 'definition',
        snippet: 'def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list:\n    # Embed query using nvidia_nim/{NVIDIA_EMBED_MODEL}\n    embed_result = embedding(model=f"nvidia_nim/{NVIDIA_EMBED_MODEL}", input=query)',
      },
      {
        filePath: 'target_project/vector_store.py',
        startLine: 13,
        endLine: 26,
        score: 0.88,
        type: 'reference',
        snippet: 'def generate_vector_id(filename: str, start_line: int, end_line: int) -> str:\n    hash_input = f"{filename}:{start_line}:{end_line}"\n    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hash_input))',
      },
      {
        filePath: 'target_project/config.py',
        startLine: 10,
        endLine: 25,
        score: 0.81,
        type: 'docstring',
        snippet: 'load_dotenv()\nPROJECT_NAME = "Sample Python Project"\nVERSION = "1.0.0"',
      },
    ],
    toolEvents: [
      { tool: 'pinecone_query', durationMs: 142, status: 'ok', summary: 'Queried serverless index with 1024-dim vector, top_k=5' },
      { tool: 'nvidia_nim_embed', durationMs: 218, status: 'ok', summary: 'Generated embedding using nvidia/nemotron-3-embed-1b' },
      { tool: 'mcp_filesystem_read', durationMs: 16, status: 'ok', summary: 'Verified target_project/query_pipeline.py AST lines 13-59' },
    ],
  },
];
