"""Multi-Agent Code Helper - Google ADK implementation.

This package implements a multi-agent AI assistant that helps developers
understand a Python codebase through RAG (Retrieval-Augmented Generation).

The system contains exactly five primary ADK agents:
1. Coordinator - receives user questions and delegates to workers
2. Code Searcher - retrieves relevant code chunks from Pinecone
3. Code Explainer - reads and explains source files via Filesystem MCP
4. Architecture Mapper - lists files and parses Python imports via AST
5. Onboarding Guide - provides project onboarding and entry points
"""

from .agent import root_agent

__all__ = ["root_agent"]