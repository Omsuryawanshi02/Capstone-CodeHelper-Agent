"""Tests for draw.io MCP client integration.

Tests tool discovery, invocation, parameter passing, error handling,
URL extraction, and graceful fallback when MCP server is unavailable.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from code_helper.tools.drawio_client import DrawioMCPClient, DrawioResponse


class TestDrawioMCPClient:
    """Unit tests for DrawioMCPClient."""

    def test_client_init_defaults(self):
        """Client should set platform-appropriate defaults."""
        client = DrawioMCPClient()
        assert client.command in ("npx.cmd", "npx")
        assert client.args == ["-y", "@drawio/mcp"]
        assert client.timeout_seconds == 15.0

    def test_extract_url(self):
        """Should extract draw.io URL from text correctly."""
        client = DrawioMCPClient()

        # Standard editor URL
        text = "Draw.io Editor URL:\nhttps://app.diagrams.net/?grid=0&edit=_blank#create=12345\nOpened in browser."
        url = client._extract_url(text)
        assert url == "https://app.diagrams.net/?grid=0&edit=_blank#create=12345"

        # Viewer URL
        text2 = "Check link: https://viewer.diagrams.net/?title=test#create=abc"
        assert client._extract_url(text2) == "https://viewer.diagrams.net/?title=test#create=abc"

        # No URL
        assert client._extract_url("No URL in this message") is None
        assert client._extract_url("") is None

    @pytest.mark.asyncio
    async def test_empty_content_rejected(self):
        """Empty mermaid or xml content should return an immediate error response."""
        client = DrawioMCPClient()

        resp_mermaid = await client.open_mermaid("")
        assert not resp_mermaid.success
        assert "cannot be empty" in resp_mermaid.error.lower()

        resp_xml = await client.open_xml("   ")
        assert not resp_xml.success
        assert "cannot be empty" in resp_xml.error.lower()

    @pytest.mark.asyncio
    async def test_mcp_tool_discovery_mocked(self):
        """Should discover tools from draw.io MCP server session."""
        mock_tool_1 = MagicMock()
        mock_tool_1.name = "open_drawio_mermaid"
        mock_tool_1.description = "Opens Mermaid diagram"
        mock_tool_1.inputSchema = {"type": "object", "properties": {"content": {"type": "string"}}}

        mock_tool_2 = MagicMock()
        mock_tool_2.name = "open_drawio_xml"
        mock_tool_2.description = "Opens XML diagram"
        mock_tool_2.inputSchema = {"type": "object", "properties": {"content": {"type": "string"}}}

        mock_tools_result = MagicMock()
        mock_tools_result.tools = [mock_tool_1, mock_tool_2]

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=mock_tools_result)

        class MockStdioContext:
            async def __aenter__(self):
                return ("read_stream", "write_stream")
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        class MockSessionContext:
            def __init__(self, r, w):
                pass
            async def __aenter__(self):
                return mock_session
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        with patch("code_helper.tools.drawio_client.stdio_client", return_value=MockStdioContext()), \
             patch("code_helper.tools.drawio_client.ClientSession", MockSessionContext):
            client = DrawioMCPClient()
            tools = await client.list_tools()
            tool_names = [t["name"] for t in tools]
            assert "open_drawio_mermaid" in tool_names
            assert "open_drawio_xml" in tool_names

            is_avail = await client.check_availability()
            assert is_avail is True

    @pytest.mark.asyncio
    async def test_open_mermaid_successful_mocked(self):
        """Should call open_drawio_mermaid tool and extract URL."""
        mock_content_item = MagicMock()
        mock_content_item.text = "Draw.io Editor URL:\nhttps://app.diagrams.net/?edit=_blank#create=xyz123"

        mock_call_result = MagicMock()
        mock_call_result.content = [mock_content_item]
        mock_call_result.isError = False

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_call_result)

        class MockStdioContext:
            async def __aenter__(self):
                return ("read", "write")
            async def __aexit__(self, *args):
                return None

        class MockSessionContext:
            def __init__(self, r, w):
                pass
            async def __aenter__(self):
                return mock_session
            async def __aexit__(self, *args):
                return None

        with patch("code_helper.tools.drawio_client.stdio_client", return_value=MockStdioContext()), \
             patch("code_helper.tools.drawio_client.ClientSession", MockSessionContext):
            client = DrawioMCPClient()
            resp = await client.open_mermaid("graph TD\n  A-->B")

            assert resp.success is True
            assert resp.url == "https://app.diagrams.net/?edit=_blank#create=xyz123"
            assert resp.tool_name == "open_drawio_mermaid"
            mock_session.call_tool.assert_called_once_with(
                "open_drawio_mermaid",
                {"content": "graph TD\n  A-->B"}
            )

    @pytest.mark.asyncio
    async def test_open_xml_successful_mocked(self):
        """Should call open_drawio_xml tool and extract URL."""
        mock_content_item = MagicMock()
        mock_content_item.text = "Draw.io Editor URL:\nhttps://app.diagrams.net/?edit=_blank#create=xml456"

        mock_call_result = MagicMock()
        mock_call_result.content = [mock_content_item]
        mock_call_result.isError = False

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_call_result)

        class MockStdioContext:
            async def __aenter__(self):
                return ("read", "write")
            async def __aexit__(self, *args):
                return None

        class MockSessionContext:
            def __init__(self, r, w):
                pass
            async def __aenter__(self):
                return mock_session
            async def __aexit__(self, *args):
                return None

        with patch("code_helper.tools.drawio_client.stdio_client", return_value=MockStdioContext()), \
             patch("code_helper.tools.drawio_client.ClientSession", MockSessionContext):
            client = DrawioMCPClient()
            resp = await client.open_xml("<mxGraphModel><root/></mxGraphModel>")

            assert resp.success is True
            assert resp.url == "https://app.diagrams.net/?edit=_blank#create=xml456"
            assert resp.tool_name == "open_drawio_xml"

    @pytest.mark.asyncio
    async def test_mcp_server_unavailable_behavior(self):
        """When MCP server fails to launch or process fails, returns graceful failure."""
        class FailingStdioContext:
            async def __aenter__(self):
                raise FileNotFoundError("npx not found")
            async def __aexit__(self, *args):
                return None

        with patch("code_helper.tools.drawio_client.stdio_client", return_value=FailingStdioContext()):
            client = DrawioMCPClient()
            resp = await client.open_mermaid("graph TD\n  A-->B")

            assert resp.success is False
            assert resp.url is None
            assert "unavailable or failed" in resp.error
            assert "FileNotFoundError" in resp.error

    @pytest.mark.asyncio
    async def test_mcp_timeout_behavior(self):
        """When MCP server exceeds timeout, returns graceful timeout response."""
        client = DrawioMCPClient(timeout_seconds=0.01)

        async def slow_call(*args, **kwargs):
            await asyncio.sleep(0.5)

        with patch.object(client, "_call_tool", side_effect=asyncio.TimeoutError):
            resp = await client.open_mermaid("graph TD\n  A-->B")
            # Should be handled gracefully
            assert resp.success is False
