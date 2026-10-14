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
from mcp.client.stdio import StdioServerParameters

from .config import validate_config, LITELLM_CHAT_MODEL
from .tools import rag_search, read_project_file, list_project_files, inspect_imports, get_project_overview


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

# Absolute path to the target project (sibling of code_helper package)
_TARGET_PROJECT_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "target_project",
    )
)

# Filesystem MCP server: run via npx, restricted to target_project
# On Windows, npx is npx.cmd; on Unix, it's npx
import platform as _platform
_NPX_CMD = "npx.cmd" if _platform.system() == "Windows" else "npx"

_FILESYSTEM_MCP_PARAMS = StdioServerParameters(
    command=_NPX_CMD,
    args=[
        "-y",
        "@modelcontextprotocol/server-filesystem",
        _TARGET_PROJECT_DIR,
    ],
)

# Build the MCP toolset (read-only filesystem operations)
# tool_filter restricts to read-only operations
_FILES_MCP_TOOLSET = McpToolset(
    connection_params=_FILESYSTEM_MCP_PARAMS,
    tool_filter=["read_file", "list_directory", "read_multiple_files"],
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
        "Route user questions to the appropriate specialist agent:\n"
        "- Code locations (function/variable/feature)          -> code_searcher\n"
        "- Explanation of a complete file                      -> code_explainer\n"
        "- Imports and architecture                           -> architecture_mapper\n"
        "- Project setup and onboarding                       -> onboarding_guide\n"
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
        "When the user asks about code location or implementation:\n"
        "1. Use the rag_search tool to find relevant code chunks from Pinecone\n"
        "2. Present the findings with filenames, line numbers, and scores\n"
        "3. Base all claims on the retrieved evidence\n"
        "4. If no useful evidence is found, admit it clearly\n"
        "5. Do not invent or hallucinate source code"
    ),
    # Register the rag_search tool for this agent
    tools=[FunctionTool(func=rag_search)],
)


# ---------------------------------------------------------------------------
# 3. Code Explainer - reads complete source files via Filesystem MCP
# ---------------------------------------------------------------------------

code_explainer = Agent(
    name="code_explainer",
    model=CHAT_MODEL,
    description=(
        "Read complete source files using Filesystem MCP. Explain imports, "
        "functions, classes, control flow, and dependencies. Distinguish "
        "observed behavior from inference. Never invent code or claim to "
        "have inspected unread files."
    ),
    instruction=(
        "When the user asks about what a particular file does:\n"
        "1. Use the Filesystem MCP to read the complete source file\n"
        "2. Explain imports, functions, classes, control flow, and dependencies\n"
        "3. Distinguish between observed code behavior and AI inference\n"
        "4. Never invent code or claim to have inspected unread files\n"
        "5. Restrict filesystem access to the target project root directory"
    ),
    # Register the read_project_file tool and Filesystem MCP for this agent
    tools=[
        FunctionTool(func=read_project_file),
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
        "Executes deterministically without language model inference."
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
        "Explain the project purpose using available evidence, identify important "
        "files and entry points, describe installation and execution steps, and "
        "recommend a reading order for beginners."
    ),
    instruction=(
        "When the user asks about project setup or onboarding:\n"
        "1. Use get_project_overview to report verified project structure\n"
        "2. Identify important files and entry points from evidence\n"
        "3. Describe installation and execution steps\n"
        "4. Recommend a reading order for beginners\n"
        "5. Distinguish documented commands from inferred commands\n"
        "6. Do not invent functionality or execution commands"
    ),
    # Register the onboarding tool for this agent
    tools=[FunctionTool(func=get_project_overview)],
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

# Export tools for external access
TOOLS = {
    "rag_search": rag_search,
    "read_project_file": read_project_file,
    "list_project_files": list_project_files,
    "inspect_imports": inspect_imports,
    "get_project_overview": get_project_overview,
}