"""Draw.io MCP Client.

Provides deterministic integration with the official draw.io MCP server:
https://github.com/jgraph/drawio-mcp
Executed via: npx -y @drawio/mcp

Exposes direct Python methods to invoke open_drawio_mermaid and open_drawio_xml
without requiring an LLM to select or invoke the tool.
"""

import asyncio
import logging
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

logger = logging.getLogger(__name__)


@dataclass
class DrawioResponse:
    """Structured response from draw.io MCP tool invocation."""
    success: bool
    url: Optional[str] = None
    raw_text: Optional[str] = None
    error: Optional[str] = None
    tool_name: Optional[str] = None
    content_sent: Optional[str] = None


class DrawioMCPClient:
    """Deterministic client for the official @drawio/mcp server."""

    def __init__(
        self,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        timeout_seconds: float = 15.0,
    ):
        """Initialize DrawioMCPClient.

        Args:
            command: Executable name (defaults to 'npx.cmd' on Windows, 'npx' on POSIX).
            args: Arguments for npx (defaults to ['-y', '@drawio/mcp']).
            timeout_seconds: Timeout for MCP operations.
        """
        if command is None:
            self.command = "npx.cmd" if sys.platform == "win32" or os.name == "nt" else "npx"
        else:
            self.command = command

        self.args = args if args is not None else ["-y", "@drawio/mcp"]
        self.timeout_seconds = timeout_seconds

    def _extract_url(self, text: str) -> Optional[str]:
        """Extract draw.io URL from text content if present."""
        if not text:
            return None
        # Match https://app.diagrams.net/... or https://viewer.diagrams.net/...
        match = re.search(r"https?://(?:app|viewer)\.diagrams\.net/[^\s\)\"\'>]+", text)
        if match:
            return match.group(0)
        return None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the draw.io MCP server.

        Returns:
            List of dictionaries describing each available tool.
        """
        try:
            if StdioServerParameters is None or ClientSession is None:
                raise ImportError("mcp package is not installed or available.")

            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=None,
            )

            async def _run():
                async with stdio_client(server_params) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        tools_result = await session.list_tools()
                        return [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": tool.inputSchema,
                            }
                            for tool in tools_result.tools
                        ]

            return await asyncio.wait_for(_run(), timeout=self.timeout_seconds)

        except Exception as e:
            logger.warning(f"Failed to list draw.io MCP tools: {e}")
            return []

    async def check_availability(self) -> bool:
        """Check if draw.io MCP server is reachable and responsive."""
        tools = await self.list_tools()
        tool_names = [t["name"] for t in tools]
        return "open_drawio_mermaid" in tool_names or "open_drawio_xml" in tool_names

    async def open_mermaid(
        self,
        mermaid_code: str,
        post_layout: Optional[str] = None,
        lightbox: bool = False,
        dark: str = "auto",
    ) -> DrawioResponse:
        """Deterministically invoke open_drawio_mermaid on draw.io MCP.

        Args:
            mermaid_code: Valid Mermaid.js diagram syntax.
            post_layout: Optional 'elk' layout.
            lightbox: Open in lightbox mode.
            dark: Dark mode setting ('auto', 'true', 'false').

        Returns:
            DrawioResponse with URL or error status.
        """
        if not mermaid_code or not mermaid_code.strip():
            return DrawioResponse(
                success=False,
                error="Mermaid code cannot be empty.",
                tool_name="open_drawio_mermaid",
            )

        tool_args: Dict[str, Any] = {"content": mermaid_code.strip()}
        if post_layout:
            tool_args["postLayout"] = post_layout
        if lightbox:
            tool_args["lightbox"] = True
        if dark in ("true", "false"):
            tool_args["dark"] = dark

        try:
            return await self._call_tool("open_drawio_mermaid", tool_args, mermaid_code)
        except asyncio.TimeoutError:
            err_msg = f"draw.io MCP server call timed out after {self.timeout_seconds}s."
            logger.warning(err_msg)
            return DrawioResponse(
                success=False,
                error=err_msg,
                tool_name="open_drawio_mermaid",
                content_sent=mermaid_code,
            )
        except Exception as e:
            err_msg = f"draw.io MCP service unavailable or failed: {type(e).__name__}: {e}"
            logger.warning(err_msg)
            return DrawioResponse(
                success=False,
                error=err_msg,
                tool_name="open_drawio_mermaid",
                content_sent=mermaid_code,
            )

    async def open_xml(
        self,
        xml_content: str,
        lightbox: bool = False,
        dark: str = "auto",
    ) -> DrawioResponse:
        """Deterministically invoke open_drawio_xml on draw.io MCP.

        Args:
            xml_content: Valid draw.io XML (mxGraphModel format).
            lightbox: Open in lightbox mode.
            dark: Dark mode setting ('auto', 'true', 'false').

        Returns:
            DrawioResponse with URL or error status.
        """
        if not xml_content or not xml_content.strip():
            return DrawioResponse(
                success=False,
                error="XML content cannot be empty.",
                tool_name="open_drawio_xml",
            )

        tool_args: Dict[str, Any] = {"content": xml_content.strip()}
        if lightbox:
            tool_args["lightbox"] = True
        if dark in ("true", "false"):
            tool_args["dark"] = dark

        try:
            return await self._call_tool("open_drawio_xml", tool_args, xml_content)
        except asyncio.TimeoutError:
            err_msg = f"draw.io MCP server call timed out after {self.timeout_seconds}s."
            logger.warning(err_msg)
            return DrawioResponse(
                success=False,
                error=err_msg,
                tool_name="open_drawio_xml",
                content_sent=xml_content,
            )
        except Exception as e:
            err_msg = f"draw.io MCP service unavailable or failed: {type(e).__name__}: {e}"
            logger.warning(err_msg)
            return DrawioResponse(
                success=False,
                error=err_msg,
                tool_name="open_drawio_xml",
                content_sent=xml_content,
            )

    async def _call_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        original_content: str,
    ) -> DrawioResponse:
        """Internal helper to execute a tool via MCP stdio."""
        if StdioServerParameters is None or ClientSession is None:
            raise ImportError("mcp package is not available.")

        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=None,
        )

        async def _run():
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, tool_args)

                    # Extract text contents
                    texts = []
                    if hasattr(result, "content") and result.content:
                        for item in result.content:
                            if hasattr(item, "text"):
                                texts.append(item.text)
                            elif isinstance(item, dict) and "text" in item:
                                texts.append(item["text"])

                    combined_text = "\n".join(texts)
                    is_error = getattr(result, "isError", False)

                    if is_error:
                        return DrawioResponse(
                            success=False,
                            error=combined_text or "draw.io MCP returned an error flag",
                            tool_name=tool_name,
                            content_sent=original_content,
                        )

                    url = self._extract_url(combined_text)
                    return DrawioResponse(
                        success=True,
                        url=url,
                        raw_text=combined_text,
                        tool_name=tool_name,
                        content_sent=original_content,
                    )

        return await asyncio.wait_for(_run(), timeout=self.timeout_seconds)
