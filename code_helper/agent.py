"""Google ADK agents for the Multi-Agent Code Helper.

Defines the root_agent and all specialized workers:
- coordinator: receives user questions and delegates to workers
- code_searcher: retrieves relevant code chunks from Pinecone
- code_explainer: reads and explains source files via Filesystem MCP
- architecture_mapper: lists files and parses Python imports via AST
- onboarding_guide: provides project onboarding and entry points
"""

import os
from typing import List

from google.adk import Agent
from google.adk.tools import FunctionTool, McpToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

from .config import validate_config, LITELLM_CHAT_MODEL
from .tools import rag_search, read_project_file, explain_code, list_project_files, inspect_imports, get_project_overview


# ---------------------------------------------------------------------------
# Shared chat model configuration (used by all agents)
# ---------------------------------------------------------------------------

if not validate_config():
    print("WARNING: Configuration validation failed. Some features may be limited.")

CHAT_MODEL = LITELLM_CHAT_MODEL


# ---------------------------------------------------------------------------
# Filesystem MCP server configuration (for Code Explainer)
#
# Uses the official Filesystem MCP server via npx.
# Access is restricted to the target_project directory only.
# The server cannot access the entire drive or read .env/secrets.
# ---------------------------------------------------------------------------

# Absolute paths to repo root and allowed directories
_REPO_ROOT = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_TARGET_PROJECT_DIR = os.path.abspath(os.path.join(_REPO_ROOT, "target_project"))
_CODE_HELPER_DIR = os.path.abspath(os.path.join(_REPO_ROOT, "code_helper"))

# Filesystem MCP server: run via npx, allowed directories: repo root, target_project, code_helper
# On Windows, npx is npx.cmd; on Unix, it's npx
import platform as _platform
_NPX_CMD = "npx.cmd" if _platform.system() == "Windows" else "npx"

_FILESYSTEM_MCP_PARAMS = StdioServerParameters(
    command=_NPX_CMD,
    args=[
        "-y",
        "@modelcontextprotocol/server-filesystem",
        _REPO_ROOT,
        _TARGET_PROJECT_DIR,
        _CODE_HELPER_DIR,
    ],
)

# Build the MCP toolset (read-only filesystem operations)
# tool_filter restricts to read-only operations
# StdioConnectionParams provides a configurable timeout (30s) instead of the default 5s
# which avoids timeouts when launching npx.cmd on Windows.
_FILES_MCP_TOOLSET = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=_FILESYSTEM_MCP_PARAMS,
        timeout=30.0,
    ),
    tool_filter=["read_file", "list_directory", "read_multiple_files"],
)


# ---------------------------------------------------------------------------
# Grounded Answer Rules & Response Format
# ---------------------------------------------------------------------------

GROUNDED_RESPONSE_FORMAT = (
    "\n\nFor code-specific answers, format your response using this structure:\n"
    "**Answer:** A direct answer to the user's question.\n"
    "**Evidence:** The relevant file path, line range and source snippet when available.\n"
    "**Explanation:** How the evidence supports the answer.\n"
    "**Limitations:** Any uncertainty, missing files, conflicting evidence or checks that remain necessary.\n"
    "Keep the answer concise for simple questions and detailed for architecture or debugging questions. Never manufacture evidence to fill a missing section."
)


# ---------------------------------------------------------------------------
# 1. Coordinator (Boss) - delegates questions to the correct worker
# ---------------------------------------------------------------------------

coordinator = Agent(
    name="coordinator",
    model=CHAT_MODEL,
    description=(
        "Receive user questions, select the correct worker, delegate through "
        "Google ADK mechanisms, and return the selected worker's response. "
        "Avoid answering questions independently instead of delegating."
    ),
    instruction=(
        "You are answering questions about an actual source-code repository. Correctness and evidence are more important than sounding confident.\n\n"
        "Route user questions according to their intent to the appropriate specialist agent:\n"
        "- Explaining any specific file, reading files via filesystem tools, or inspecting coordinator/agent configurations (e.g. indexer.py, main.py, config.py, code_helper/agent.py) -> code_explainer\n"
        "- Searching for where a specific function, class, variable, or feature is implemented -> code_searcher\n"
        "- Module imports, dependency graphs, and AST architecture -> architecture_mapper\n"
        "- Overall project setup, onboarding guide, and repository-wide overview -> onboarding_guide\n\n"
        "Coordinator Grounding Rules:\n"
        "- Route questions according to their intent.\n"
        "- Explaining or asking to read/inspect any specific filename (.py) or agent source file (such as the coordinator's Python source file) MUST ALWAYS be delegated to code_explainer.\n"
        "- Do not independently fabricate the answer when a specialist should handle it.\n"
        "- Preserve the specialist's evidence and uncertainty.\n"
        "- Do not misrepresent which worker executed the task.\n"
        "Always delegate to a worker instead of answering independently."
    ),
    # Coordinator does not need direct tools; it delegates to workers
)


# ---------------------------------------------------------------------------
# 2. Code Searcher - retrieves relevant chunks from Pinecone
# ---------------------------------------------------------------------------

code_searcher = Agent(
    name="code_searcher",
    model=CHAT_MODEL,
    description=(
        "Retrieve relevant code chunks from Pinecone using rag_search tool. "
        "Explain where code is located with filenames and line ranges. "
        "Base claims on retrieved evidence and admit when search finds no useful evidence."
    ),
    instruction=(
        "You are the Code Searcher agent answering questions about an actual source-code repository.\n\n"
        "Code Searcher Grounding Rules:\n"
        "1. Use `rag_search` for questions about code locations and implementations.\n"
        "2. Inspect the returned filenames, line ranges and snippets.\n"
        "3. Do not invent filenames, line numbers, functions, classes or variables.\n"
        "4. If retrieved chunks are unrelated, refine the search using relevant technical terms and identifiers.\n"
        "5. Do not claim that a feature exists merely because its name appears in a document.\n"
        "6. If no relevant evidence is found after reasonable searches, explicitly say so.\n"
        "7. Distinguish source-code facts from inferences.\n"
        "8. If the user asks about project onboarding or setup, transfer to 'onboarding_guide'.\n"
        "9. If the user asks about file connections or architecture, transfer to 'architecture_mapper'.\n"
        "10. If the user asks to explain a complete source file, transfer to 'code_explainer'.\n"
        + GROUNDED_RESPONSE_FORMAT
    ),
    tools=[FunctionTool(func=rag_search)],
)


# ---------------------------------------------------------------------------
# 3. Code Explainer - reads complete source files via Filesystem MCP
# ---------------------------------------------------------------------------

code_explainer = Agent(
    name="code_explainer",
    model=CHAT_MODEL,
    description=(
        "Read and explain specific source files (e.g., indexer.py, main.py, config.py, query_pipeline.py, vector_store.py, or code_helper/agent.py). "
        "Explains what any individual file does, its purpose, functions, classes, imports, agent configuration, control flow, and dependencies "
        "using read_project_file or Filesystem MCP. Always use this agent when the user asks "
        "about a particular file's purpose, role, or implementation, or requests reading source files via filesystem tools."
    ),
    instruction=(
        "You are the Code Explainer agent answering questions about an actual source-code repository.\n\n"
        "Code Explainer Grounding Rules:\n"
        "1. Read the actual file through `read_project_file`, `explain_code`, or Filesystem MCP `read_file`.\n"
        "   - Target application source files reside in `target_project/` (e.g., `main.py`, `config.py`, `indexer.py`, `query_pipeline.py`, `vector_store.py`).\n"
        "   - Multi-agent framework source files reside in `code_helper/`.\n"
        "   - The coordinator and worker agent definitions are implemented in `code_helper/agent.py`. If the user asks to read the coordinator's Python source file or summarize its imports and configuration, read `code_helper/agent.py`.\n"
        "2. Explain the observed implementation, imports, functions, control flow, agent configurations, and dependencies.\n"
        "3. Do not describe intended behavior as implemented behavior without source evidence.\n"
        "4. Include relevant filenames and line numbers where available.\n"
        "5. Do not infer runtime behavior that cannot be established from static inspection.\n"
        "6. Do NOT transfer to 'code_explainer' as you are already code_explainer.\n"
        "7. If the user asks where a function is located, transfer to 'code_searcher'.\n"
        "8. If the user asks about architecture or imports, transfer to 'architecture_mapper'.\n"
        "9. If the user asks about project setup or onboarding, transfer to 'onboarding_guide'.\n"
        + GROUNDED_RESPONSE_FORMAT
    ),
    # Register the read_project_file tool, explain_code alias, and Filesystem MCP for this agent
    tools=[
        FunctionTool(func=read_project_file),
        FunctionTool(func=explain_code),
        _FILES_MCP_TOOLSET,
    ],
)


# ---------------------------------------------------------------------------
# 4. Architecture Mapper - lists files and parses Python imports via AST
# ---------------------------------------------------------------------------

from .architecture_agent import ArchitectureMapperAgent

architecture_mapper = ArchitectureMapperAgent(
    name="architecture_mapper",
    description=(
        "Deterministic Python architecture mapper. Discovers source files, "
        "extracts imports and AST definitions, builds module dependency graphs, "
        "generates verified Mermaid and draw.io diagrams, and inspects code changes. "
        "Executes deterministically without language model inference. Generates "
        "diagram edges only from validated relationships."
    ),
    tools=[
        FunctionTool(func=list_project_files),
        FunctionTool(func=inspect_imports),
    ],
)



# ---------------------------------------------------------------------------
# 5. Onboarding Guide - provides project onboarding and entry points
# ---------------------------------------------------------------------------

onboarding_guide = Agent(
    name="onboarding_guide",
    model=CHAT_MODEL,
    description=(
        "High-level repository onboarding, installation, prerequisites, execution commands, and project entry points. "
        "Provides repo-level overview for newcomers. Does NOT explain specific source code files."
    ),
    instruction=(
        "You are the Onboarding Guide agent answering questions about an actual source-code repository.\n\n"
        "Onboarding Guide Grounding Rules:\n"
        "1. Use repository files and verified setup instructions via `get_project_overview`.\n"
        "2. Do not invent installation commands, environment variables, entry points or features.\n"
        "3. Label unverified instructions as unverified.\n"
        "4. If the user asks where a function/variable/code is located, IMMEDIATELY transfer to 'code_searcher'.\n"
        "5. If the user asks about imports, connections between files, or architecture, IMMEDIATELY transfer to 'architecture_mapper'.\n"
        "6. If the user asks to explain a specific file, what a file does, or the purpose of any file (e.g., indexer.py, main.py), IMMEDIATELY transfer to 'code_explainer' or use `read_project_file` to inspect it.\n"
        "7. NEVER output raw JSON function call strings or phrases like 'The function call ... best answers'. Write natural, helpful explanations.\n"
        + GROUNDED_RESPONSE_FORMAT
    ),
    # Register the onboarding tool and read_project_file for this agent
    tools=[
        FunctionTool(func=get_project_overview),
        FunctionTool(func=read_project_file),
    ],
)


# ---------------------------------------------------------------------------
# Root agent discovery - Google ADK requires root_agent attribute
# ---------------------------------------------------------------------------

root_agent = coordinator

# Attach worker agents as sub-agents of the coordinator for ADK discovery
coordinator.sub_agents = [
    code_searcher,
    code_explainer,
    architecture_mapper,
    onboarding_guide,
]
# Ensure Google ADK internal parent-child relationships are set for all sub-agents
coordinator._BaseAgent__set_parent_agent_for_sub_agents()



# Export tools for external access
TOOLS = {
    "rag_search": rag_search,
    "read_project_file": read_project_file,
    "explain_code": explain_code,
    "list_project_files": list_project_files,
    "inspect_imports": inspect_imports,
    "get_project_overview": get_project_overview,
}