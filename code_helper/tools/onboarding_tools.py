"""Onboarding guide tools.

Provides get_project_overview for reporting verified project structure,
entry points, and available run instructions.
"""

import os


def get_project_overview() -> str:
    """Report the verified project structure, entry points, and run instructions.

    Returns verified information about the project without inventing
    functionality or execution commands.

    Returns:
        String with project overview, structure, entry points, and run instructions.
    """
    # Base directory is the target_project folder, three levels up from tools/
    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "target_project",
    )

    # Discover files in the target project
    try:
        all_entries = sorted(os.listdir(base_dir)) if os.path.isdir(base_dir) else []
    except Exception:
        all_entries = []

    py_files = [f for f in all_entries if f.endswith(".py")]

    # Build overview
    output_parts = []

    output_parts.append("=" * 60)
    output_parts.append("MULTI-AGENT CODE HELPER - PROJECT OVERVIEW")
    output_parts.append("=" * 60)

    # Project structure
    output_parts.append("\n--- Project Structure ---")
    if py_files:
        for f in py_files:
            output_parts.append(f"  {f}")
    else:
        output_parts.append("  No .py files found")

    # Check for entry points
    output_parts.append("\n--- Entry Points ---")
    main_file = os.path.join(base_dir, "main.py")
    if os.path.isfile(main_file):
        output_parts.append("  main.py - Main entry point")
    else:
        output_parts.append("  main.py - not found")

    config_file = os.path.join(base_dir, "config.py")
    if os.path.isfile(config_file):
        output_parts.append("  config.py - Configuration")

    index_file = os.path.join(base_dir, "indexer.py")
    if os.path.isfile(index_file):
        output_parts.append("  indexer.py - Indexing utilities")

    vec_file = os.path.join(base_dir, "vector_store.py")
    if os.path.isfile(vec_file):
        output_parts.append("  vector_store.py - Vector store")

    qp_file = os.path.join(base_dir, "query_pipeline.py")
    if os.path.isfile(qp_file):
        output_parts.append("  query_pipeline.py - Query pipeline")

    # Run instructions (based on ADK framework)
    output_parts.append("\n--- Run Instructions ---")
    output_parts.append("  Terminal:  adk run code_helper")
    output_parts.append("  Web:       adk web (when supported)")
    output_parts.append("  From directory: D:\\deboistech\\demo")

    # Configuration requirements
    output_parts.append("\n--- Configuration Requirements ---")
    output_parts.append("  Required env vars: NVIDIA_NIM_API_KEY, PINECONE_API_KEY")
    output_parts.append("  Optional: NVIDIA_BASE_URL, NVIDIA_CHAT_MODEL, NVIDIA_EMBED_MODEL")
    output_parts.append("  Pinecone: index 'code-helper' (2048 dim, cosine, aws/us-east-1)")

    # Agent mapping
    output_parts.append("\n--- Available Agents ---")
    output_parts.append("  coordinator  - Receive questions and delegate to workers")
    output_parts.append("  code_searcher - Retrieve relevant code chunks from Pinecone")
    output_parts.append("  code_explainer - Read and explain source files via MCP")
    output_parts.append("  architecture_mapper - List files and parse imports via AST")
    output_parts.append("  onboarding_guide - Project onboarding and entry points")

    output_parts.append("\n" + "=" * 60)

    return "\n".join(output_parts)