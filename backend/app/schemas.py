"""Pydantic schemas for request validation and response contracts."""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: Literal["ok", "degraded", "unhealthy"]
    backend_running: bool = True
    adk_reachable: bool = False
    adk_app_name: str
    config_valid: bool = False
    timestamp: float


class CreateSessionRequest(BaseModel):
    """Session creation request schema."""
    title: Optional[str] = Field(default=None, max_length=100, description="Optional conversation title")
    user_id: Optional[str] = Field(default=None, max_length=100, description="Optional user identifier")


class SessionResponse(BaseModel):
    """Session creation and detail response schema."""
    session_id: str
    app_name: str
    user_id: str
    title: Optional[str] = None
    created_at: float


class SessionListItem(BaseModel):
    """Summary of a conversation session."""
    session_id: str
    title: str
    created_at: float
    last_message_at: Optional[float] = None
    message_count: int = 0


class SourceMetadata(BaseModel):
    """Grounding source reference information."""
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    snippet: Optional[str] = None
    score: Optional[float] = None


class ChatMessageRequest(BaseModel):
    """Chat submission request schema."""
    session_id: str = Field(..., min_length=1, max_length=200, description="Session ID")
    message: str = Field(..., min_length=1, max_length=10000, description="User question or prompt")
    user_id: Optional[str] = Field(default=None, max_length=100)


class ChatMessageResponse(BaseModel):
    """Synchronous chat response schema."""
    session_id: str
    message: str
    agent_name: Optional[str] = None
    sources: List[SourceMetadata] = Field(default_factory=list)


class NormalizedSSEEvent(BaseModel):
    """Normalized Server-Sent Event for browser streaming."""
    type: Literal["status", "agent_activity", "token", "message", "source", "done", "error"]
    session_id: str
    text: Optional[str] = None
    agent_name: Optional[str] = None
    activity: Optional[str] = None
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    snippet: Optional[str] = None
    score: Optional[float] = None
    error: Optional[str] = None
