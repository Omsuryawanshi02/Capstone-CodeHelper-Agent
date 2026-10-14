"""Event adapter to normalize Google ADK events into the frontend SSE contract.

Converts raw ADK events into:
- status: connection and processing lifecycle
- agent_activity: grounded active worker and sanitized tool actions
- token: incremental text tokens (if available)
- message: full response text update
- source: grounded source code references with file path and line numbers
- done: completion marker
- error: sanitized error messages
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Iterator
from .schemas import NormalizedSSEEvent, SourceMetadata

logger = logging.getLogger(__name__)

# Map ADK agents to clear user-facing activity labels
AGENT_ACTIVITY_MAP = {
    "coordinator": "Routing request to specialist agent...",
    "code_searcher": "Searching indexed code in Pinecone...",
    "code_explainer": "Reading source file via Filesystem MCP...",
    "architecture_mapper": "Analyzing imports and module structure via AST...",
    "onboarding_guide": "Generating project onboarding guide...",
}

# Regex to extract structured source evidence from rag_search tool outputs
RAG_RESULT_PATTERN = re.compile(
    r"Score:\s*(?P<score>[0-9.]+)\s*\|\s*File:\s*(?P<filename>[^\s|]+)\s*\|\s*Lines:\s*(?P<start>[0-9?]+)-(?P<end>[0-9?]+)",
    re.IGNORECASE,
)


class EventAdapter:
    """Stateful adapter for normalizing ADK event streams per session turn."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_agent: Optional[str] = None
        self.accumulated_text: str = ""
        self.emitted_sources: set[Tuple[str, Optional[int], Optional[int]]] = set()
        self.turn_completed: bool = False

    def process_raw_adk_event(self, raw_data: Dict[str, Any]) -> List[NormalizedSSEEvent]:
        """Convert a single parsed ADK Event JSON into a list of normalized SSE events."""
        events: List[NormalizedSSEEvent] = []

        # 1. Check for error conditions
        error_msg = raw_data.get("errorMessage") or raw_data.get("error_message")
        if error_msg:
            # Sanitize error message to avoid exposing raw credentials or internal paths
            sanitized = self._sanitize_error(str(error_msg))
            return [
                NormalizedSSEEvent(
                    type="error",
                    session_id=self.session_id,
                    error=sanitized,
                )
            ]

        # 2. Extract author/agent activity
        author = raw_data.get("author")
        if author and author != self.current_agent:
            self.current_agent = author
            activity_text = AGENT_ACTIVITY_MAP.get(
                author, f"Agent '{author}' is working on your request..."
            )
            events.append(
                NormalizedSSEEvent(
                    type="agent_activity",
                    session_id=self.session_id,
                    agent_name=author,
                    activity=activity_text,
                )
            )

        # 3. Check for tool / function calls in actions or content
        events.extend(self._extract_tool_activity_and_sources(raw_data))

        # 4. Extract content and text tokens
        content = raw_data.get("content", {})
        parts = content.get("parts", []) if isinstance(content, dict) else []
        for part in parts:
            if not isinstance(part, dict):
                continue

            text_chunk = part.get("text")
            if text_chunk:
                is_partial = raw_data.get("partial", False)
                if is_partial:
                    # Incremental token streaming
                    events.append(
                        NormalizedSSEEvent(
                            type="token",
                            session_id=self.session_id,
                            text=text_chunk,
                            agent_name=self.current_agent,
                        )
                    )
                self.accumulated_text += text_chunk

        # If turn is completed or complete message is ready
        turn_complete = raw_data.get("turnComplete") or raw_data.get("turn_complete", False)
        if turn_complete:
            self.turn_completed = True
            # Emit final message state if we have accumulated text
            if self.accumulated_text:
                events.append(
                    NormalizedSSEEvent(
                        type="message",
                        session_id=self.session_id,
                        text=self.accumulated_text,
                        agent_name=self.current_agent,
                    )
                )
            events.append(
                NormalizedSSEEvent(
                    type="done",
                    session_id=self.session_id,
                )
            )

        return events

    def _extract_tool_activity_and_sources(self, raw_data: Dict[str, Any]) -> List[NormalizedSSEEvent]:
        """Inspect actions, function calls, and function responses for grounded activity and sources."""
        events: List[NormalizedSSEEvent] = []

        # Check content parts for function calls or function responses
        content = raw_data.get("content", {})
        parts = content.get("parts", []) if isinstance(content, dict) else []

        for part in parts:
            if not isinstance(part, dict):
                continue

            # Tool Invocation (FunctionCall)
            fn_call = part.get("functionCall") or part.get("function_call")
            if fn_call and isinstance(fn_call, dict):
                fn_name = fn_call.get("name", "tool")
                args = fn_call.get("args", {})

                activity_desc = self._format_tool_call_activity(fn_name, args)
                events.append(
                    NormalizedSSEEvent(
                        type="agent_activity",
                        session_id=self.session_id,
                        agent_name=self.current_agent,
                        activity=activity_desc,
                    )
                )

                # If reading a specific file, emit early source reference
                file_arg = args.get("file_path") or args.get("path")
                if file_arg and isinstance(file_arg, str) and file_arg.endswith(".py"):
                    source_key = (file_arg, None, None)
                    if source_key not in self.emitted_sources:
                        self.emitted_sources.add(source_key)
                        events.append(
                            NormalizedSSEEvent(
                                type="source",
                                session_id=self.session_id,
                                file_path=file_arg,
                                snippet=f"Referenced by {fn_name}",
                            )
                        )

            # Tool Response (FunctionResponse)
            fn_response = part.get("functionResponse") or part.get("function_response")
            if fn_response and isinstance(fn_response, dict):
                resp_name = fn_response.get("name", "")
                response_data = fn_response.get("response", {})
                
                # Check for RAG search results containing Score/File/Lines
                text_content = ""
                if isinstance(response_data, dict):
                    text_content = str(response_data.get("output", "") or response_data.get("content", ""))
                elif isinstance(response_data, str):
                    text_content = response_data

                if text_content and ("Score:" in text_content or "File:" in text_content):
                    for match in RAG_RESULT_PATTERN.finditer(text_content):
                        fn = match.group("filename")
                        start_str = match.group("start")
                        end_str = match.group("end")
                        score_str = match.group("score")

                        start_line = int(start_str) if start_str.isdigit() else None
                        end_line = int(end_str) if end_str.isdigit() else None
                        score = float(score_str) if score_str else None

                        source_key = (fn, start_line, end_line)
                        if source_key not in self.emitted_sources:
                            self.emitted_sources.add(source_key)
                            events.append(
                                NormalizedSSEEvent(
                                    type="source",
                                    session_id=self.session_id,
                                    file_path=fn,
                                    start_line=start_line,
                                    end_line=end_line,
                                    score=score,
                                    snippet=f"Retrieved from Pinecone (score: {score})",
                                )
                            )

        return events

    def _format_tool_call_activity(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Produce a clean, user-friendly activity description without exposing sensitive details."""
        if tool_name == "rag_search":
            query = args.get("query", "")
            short_query = f' "{query[:40]}..."' if query else ""
            return f"Executing vector search in Pinecone{short_query}"
        elif tool_name in ("read_project_file", "read_file"):
            fpath = args.get("file_path") or args.get("path", "")
            return f"Reading source file: {fpath}"
        elif tool_name == "inspect_imports":
            fpath = args.get("file_path", "")
            return f"Inspecting imports & AST structure in: {fpath}"
        elif tool_name in ("list_project_files", "list_directory"):
            return "Scanning repository files..."
        elif tool_name == "get_project_overview":
            return "Reviewing verified project structure..."
        else:
            return f"Executing tool: {tool_name}"

    def _sanitize_error(self, message: str) -> str:
        """Remove sensitive tokens, URLs with credentials, and long tracebacks from error messages."""
        # Redact anything looking like an API key
        sanitized = re.sub(r"(nvapi-[a-zA-Z0-9_-]+|pcsk_[a-zA-Z0-9_-]+|[a-f0-9]{32,})", "[REDACTED_KEY]", message)
        # Limit length to avoid huge tracebacks leaking internal details
        if len(sanitized) > 300:
            sanitized = sanitized[:300] + "... (details logged securely on server)"
        return sanitized
