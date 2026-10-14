"""Tests for deterministic, no-LLM Architecture Mapper.

Validates:
- AST import extraction
- Stable diagram generation for identical input
- Accurate edges based on actual imports
- Mermaid/XML escaping
- Syntax error handling
- Path restrictions
- Full ArchitectureMapperAgent execution with LLM disabled/mocked to fail
"""

import os
import shutil
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from google.adk.events import Event
from google.genai.types import Content, Part

from code_helper.tools.architecture_tools import (
    build_dependency_graph,
    generate_mermaid_diagram,
    generate_drawio_xml,
    generate_architecture_report,
    inspect_imports,
    list_project_files,
    sanitize_mermaid_id,
)
from code_helper.architecture_agent import ArchitectureMapperAgent
from code_helper.tools.drawio_client import DrawioResponse


class TestDeterministicGraphAndDiagrams:
    """Tests for deterministic graph building and diagram generation."""

    @pytest.fixture
    def sample_codebase(self):
        """Create a temporary multi-module Python codebase."""
        temp_dir = tempfile.mkdtemp(prefix="test_arch_codebase_")
        try:
            # File 1: config.py
            with open(os.path.join(temp_dir, "config.py"), "w") as f:
                f.write("API_KEY = 'secret'\nDEBUG = True\n")

            # File 2: db.py (imports config)
            with open(os.path.join(temp_dir, "db.py"), "w") as f:
                f.write("import config\nclass Database:\n    def connect(self):\n        pass\n")

            # File 3: service.py (imports db and config)
            with open(os.path.join(temp_dir, "service.py"), "w") as f:
                f.write("from db import Database\nimport config\ndef run_service():\n    db = Database()\n")

            # File 4: broken.py (syntax error)
            with open(os.path.join(temp_dir, "broken.py"), "w") as f:
                f.write("def broken(\n    missing closing paren")

            yield temp_dir
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_dependency_graph_accurate_edges(self, sample_codebase):
        """Should detect accurate edges based on actual imports."""
        graph = build_dependency_graph(project_root=sample_codebase)

        nodes = graph["nodes"]
        edges = graph["edges"]
        syntax_errors = graph["syntax_errors"]

        assert "config" in nodes
        assert "db" in nodes
        assert "service" in nodes

        # Check syntax error reported for broken.py
        assert "broken" in syntax_errors
        assert "Line 1" in syntax_errors["broken"]

        # Check edges
        edge_pairs = [(e["source"], e["target"]) for e in edges]
        assert ("db", "config") in edge_pairs
        assert ("service", "db") in edge_pairs
        assert ("service", "config") in edge_pairs

    def test_stable_diagram_generation_identical_input(self, sample_codebase):
        """Diagram generation must produce identical strings on repeated runs."""
        graph1 = build_dependency_graph(project_root=sample_codebase)
        mermaid1 = generate_mermaid_diagram(graph1)
        xml1 = generate_drawio_xml(graph1)

        graph2 = build_dependency_graph(project_root=sample_codebase)
        mermaid2 = generate_mermaid_diagram(graph2)
        xml2 = generate_drawio_xml(graph2)

        assert mermaid1 == mermaid2
        assert xml1 == xml2

    def test_mermaid_escaping_and_valid_syntax(self):
        """Mermaid generator should sanitize IDs and escape labels properly."""
        mock_graph = {
            "nodes": {
                "sub-pkg.my_module": {
                    "file": "sub-pkg/my_module.py",
                    "classes": ["MyClass"],
                    "functions": ["my_func"],
                }
            },
            "edges": [],
        }

        mermaid = generate_mermaid_diagram(mock_graph)
        assert "graph TD" in mermaid
        assert "sub_pkg_my_module" in mermaid  # sanitized ID
        assert "sub-pkg/my_module.py" in mermaid

    def test_drawio_xml_escaping(self):
        """Draw.io XML generator should escape XML entities."""
        mock_graph = {
            "nodes": {
                "mod&special<chars>": {
                    "file": "mod&special<chars>.py",
                    "classes": [],
                    "functions": [],
                }
            },
            "edges": [],
        }

        xml = generate_drawio_xml(mock_graph)
        assert "<mxGraphModel" in xml
        assert "</mxGraphModel>" in xml
        # Ampersands and brackets should be escaped
        assert "&amp;" in xml or "&#" in xml
        assert "<chars>" not in xml  # must be escaped

    def test_inspect_imports_path_traversal_restriction(self):
        """inspect_imports should reject traversal outside target project."""
        res1 = inspect_imports("../../../etc/passwd.py")
        assert "Error: Path traversal" in res1

        res2 = inspect_imports("/absolute/path.py")
        assert "Error: Path traversal" in res2

        res3 = inspect_imports("invalid.txt")
        assert "Error: Only .py files" in res3


class TestArchitectureMapperNoLLM:
    """Acceptance tests verifying Architecture Mapper runs without any LLM."""

    @pytest.mark.asyncio
    async def test_agent_execution_with_llm_calls_disabled(self):
        """Agent must execute purely deterministically when LLMs are disabled/mocked to fail."""
        # Create mock invocation context
        mock_ctx = MagicMock()
        mock_ctx.user_content = Content(
            role="user",
            parts=[Part(text="Show module dependencies and generate drawio diagram")],
        )
        mock_ctx.session = MagicMock()
        mock_ctx.session.events = []

        # Mock DrawioMCPClient to return a verified diagram URL
        mock_drawio_client = MagicMock()
        mock_drawio_client.open_mermaid = AsyncMock(
            return_value=DrawioResponse(
                success=True,
                url="https://app.diagrams.net/?edit=_blank#create=mock_diagram_123",
                tool_name="open_drawio_mermaid",
            )
        )

        agent = ArchitectureMapperAgent(
            name="architecture_mapper",
            description="Deterministic architecture mapper",
            drawio_client=mock_drawio_client,
        )

        # Ensure no LLM or chat model is ever called
        with patch("google.adk.models.BaseLlm", side_effect=RuntimeError("LLM MUST NOT BE CALLED")), \
             patch("httpx.AsyncClient.post", side_effect=RuntimeError("NO EXTERNAL API CALLS")):

            events = []
            async for ev in agent._run_async_impl(mock_ctx):
                events.append(ev)

            assert len(events) == 1
            event = events[0]

            assert event.author == "architecture_mapper"
            assert event.turn_complete is True
            assert event.custom_metadata["llm_used"] is False
            assert event.custom_metadata["deterministic_execution"] is True
            assert event.custom_metadata["diagram_url"] == "https://app.diagrams.net/?edit=_blank#create=mock_diagram_123"

            # Check text output contains verified sections
            text = event.content.parts[0].text
            assert "Verified Architecture Report" in text
            assert "https://app.diagrams.net/?edit=_blank#create=mock_diagram_123" in text
            assert "Mermaid Architecture Definition" in text
            assert "Limitations of Static Analysis" in text

    @pytest.mark.asyncio
    async def test_agent_execution_when_mcp_is_unavailable(self):
        """Agent must return local Mermaid analysis cleanly when draw.io MCP is unavailable."""
        mock_ctx = MagicMock()
        mock_ctx.user_content = Content(
            role="user",
            parts=[Part(text="What is the architecture of the project?")],
        )
        mock_ctx.session = MagicMock()
        mock_ctx.session.events = []

        mock_drawio_client = MagicMock()
        mock_drawio_client.open_mermaid = AsyncMock(
            return_value=DrawioResponse(
                success=False,
                error="Connection refused: drawio MCP server is not running.",
                tool_name="open_drawio_mermaid",
            )
        )

        agent = ArchitectureMapperAgent(
            name="architecture_mapper",
            description="Deterministic architecture mapper",
            drawio_client=mock_drawio_client,
        )

        events = []
        async for ev in agent._run_async_impl(mock_ctx):
            events.append(ev)

        assert len(events) == 1
        event = events[0]
        text = event.content.parts[0].text

        assert "Draw.io MCP Diagram Service Unavailable" in text
        assert "Connection refused" in text
        assert "```mermaid" in text
        assert event.custom_metadata["mcp_success"] is False
