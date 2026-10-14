"""Deterministic Architecture Mapper Agent for Google ADK.

This agent is a custom Google ADK BaseAgent (NOT an LlmAgent).
It does not initialize, invoke, or depend on any LLM, chat model,
embedding service, or vector store in its execution path.

Execution Pipeline:
1. Extract user question from InvocationContext.
2. Parse request using deterministic Python keyword/regex rules.
3. Read authorized Python source files using pathlib/os.
4. Parse AST to extract imports, functions, classes, and syntax errors.
5. Construct a module dependency graph.
6. Generate deterministic Mermaid syntax or draw.io XML.
7. Invoke the official @drawio/mcp server directly via DrawioMCPClient.
8. Yield a structured ADK Event containing the verified architecture report.
"""

import logging
import os
import re
from typing import AsyncGenerator, Dict, Any, List, Optional
from pydantic import Field

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai.types import Content, Part

from .tools.architecture_tools import (
    get_default_project_root,
    build_dependency_graph,
    generate_mermaid_diagram,
    generate_drawio_xml,
    generate_architecture_report,
)
from .tools.drawio_client import DrawioMCPClient
from .tools.code_change_analyzer import CodeChangeAnalyzer

logger = logging.getLogger(__name__)


class ArchitectureMapperAgent(BaseAgent):
    """Deterministic, genuinely no-LLM architecture mapping worker."""

    tools: list = Field(default_factory=list)
    drawio_client: Optional[Any] = Field(default=None)
    project_root_override: Optional[str] = Field(default=None)
    repo_root_override: Optional[str] = Field(default=None)

    def _get_project_root(self) -> str:
        """Resolve the project directory to analyze."""
        if self.project_root_override:
            return os.path.abspath(self.project_root_override)
        return get_default_project_root()

    def _get_repo_root(self) -> str:
        """Resolve the Git repository root."""
        if self.repo_root_override:
            return os.path.abspath(self.repo_root_override)
        return os.path.abspath(
            os.path.dirname(os.path.dirname(__file__))
        )

    def _extract_user_request(self, ctx: InvocationContext) -> str:
        """Deterministically extract the latest user message from context."""
        text_parts = []

        if ctx.user_content and ctx.user_content.parts:
            for part in ctx.user_content.parts:
                if hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

        if not text_parts and hasattr(ctx, "session") and ctx.session:
            events = getattr(ctx.session, "events", []) or []
            for ev in reversed(events):
                is_user = (
                    getattr(ev, "author", None) == "user"
                    or (hasattr(ev, "content") and ev.content and getattr(ev.content, "role", None) == "user")
                )
                if is_user and hasattr(ev, "content") and ev.content and ev.content.parts:
                    for p in ev.content.parts:
                        if hasattr(p, "text") and p.text:
                            text_parts.append(p.text)
                    if text_parts:
                        break

        return " ".join(text_parts).strip()

    def _parse_request_rules(self, query: str) -> Dict[str, Any]:
        """Classify user query using deterministic keyword and regex rules."""
        q_lower = query.lower()

        # 1. Determine diagram type
        diagram_type = "dependencies"  # default
        if any(w in q_lower for w in ["impact", "change", "diff", "modified", "affect", "regress"]):
            diagram_type = "impact"
        elif any(w in q_lower for w in ["class", "classes", "function", "functions", "method"]):
            diagram_type = "classes_functions"
        elif any(w in q_lower for w in ["file", "files", "structure"]):
            diagram_type = "files"
        elif any(w in q_lower for w in ["architecture", "overview", "system", "component"]):
            diagram_type = "architecture"
        elif "before" in q_lower and "after" in q_lower:
            diagram_type = "comparison"

        # 2. Extract optional filter
        filter_pattern = None
        filter_match = re.search(r"(?:filter|for|in|module|file)\s+[:=]?\s*['\"]?([a-zA-Z0-9_\-\./]+)['\"]?", q_lower)
        if filter_match:
            candidate = filter_match.group(1).strip()
            # Ignore common query stop words and project names
            if candidate not in {
                "the", "a", "an", "this", "project", "code", "repo", "all",
                "diagram", "target_project", "target", "source", "python"
            }:
                filter_pattern = candidate

        # 3. Check if change analysis is explicitly desired
        analyze_changes = diagram_type == "impact" or any(
            w in q_lower for w in ["what changed", "git status", "git diff", "recent change", "staged", "unstaged"]
        )

        return {
            "diagram_type": diagram_type,
            "filter_pattern": filter_pattern,
            "analyze_changes": analyze_changes,
        }

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Deterministic Google ADK execution implementation.

        Yields ADK Events without any LLM calls.
        """
        user_query = self._extract_user_request(ctx)
        parsed = self._parse_request_rules(user_query)

        diagram_type = parsed["diagram_type"]
        filter_pattern = parsed["filter_pattern"]
        analyze_changes = parsed["analyze_changes"]

        project_root = self._get_project_root()
        repo_root = self._get_repo_root()

        impacted_modules: List[str] = []
        change_report_summary: Optional[str] = None

        # Step A: Perform deterministic Git and AST change analysis if requested
        if analyze_changes:
            try:
                change_analyzer = CodeChangeAnalyzer(repo_root=repo_root)
                change_result = change_analyzer.analyze_changes(target_subpath="target_project")
                if change_result.has_changes:
                    impacted_modules = change_result.impacted_modules
                    change_report_summary = change_result.summary
                else:
                    change_report_summary = change_result.summary
            except Exception as e:
                logger.warning(f"Change analysis encountered error: {e}")
                change_report_summary = f"Notice: Change analysis could not complete: {e}"

        # Step B: Build verified dependency graph using Python AST
        try:
            graph = build_dependency_graph(
                project_root=project_root,
                filter_pattern=filter_pattern,
            )
        except Exception as e:
            err_msg = f"Failed to build dependency graph: {e}"
            yield Event(
                author=self.name,
                content=Content(role="model", parts=[Part(text=err_msg)]),
                turn_complete=True,
                custom_metadata={"worker": self.name, "error": err_msg},
            )
            return

        # Step C: Generate deterministic Mermaid diagram syntax
        mermaid_code = generate_mermaid_diagram(
            graph=graph,
            diagram_type=diagram_type,
            impacted_modules=impacted_modules,
        )

        # Step D: Deterministically invoke draw.io MCP client
        client = self.drawio_client
        if client is None:
            client = DrawioMCPClient()

        diagram_url: Optional[str] = None
        mcp_error: Optional[str] = None

        try:
            mcp_response = await client.open_mermaid(mermaid_code)
            if mcp_response.success and mcp_response.url:
                diagram_url = mcp_response.url
            elif not mcp_response.success:
                mcp_error = mcp_response.error or "draw.io MCP returned an unsuccessful response."
        except Exception as e:
            mcp_error = f"Exception invoking draw.io MCP: {e}"

        # Step E: Produce verified architecture report
        arch_report = generate_architecture_report(
            graph=graph,
            diagram_url=diagram_url,
            mcp_error=mcp_error,
            mermaid_code=mermaid_code,
            diagram_type=diagram_type,
            impacted_modules=impacted_modules,
        )

        # Combine reports if change analysis was performed
        final_output_parts = [arch_report]
        if change_report_summary:
            final_output_parts.append("\n---\n")
            final_output_parts.append(change_report_summary)

        final_text = "\n".join(final_output_parts)

        # Step F: Yield structured ADK Event
        custom_metadata = {
            "worker": self.name,
            "diagram_type": diagram_type,
            "diagram_url": diagram_url,
            "mcp_success": diagram_url is not None,
            "deterministic_execution": True,
            "llm_used": False,
        }

        yield Event(
            author=self.name,
            content=Content(role="model", parts=[Part(text=final_text)]),
            turn_complete=True,
            custom_metadata=custom_metadata,
        )
