"""Session management routes."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Query
from ..schemas import CreateSessionRequest, SessionResponse, SessionListItem

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: Request,
    req: Optional[CreateSessionRequest] = None,
) -> SessionResponse:
    """Create a new conversation session."""
    session_service = request.app.state.session_service
    title = req.title if req else None
    user_id = req.user_id if req else None
    return await session_service.create_session(title=title, user_id=user_id)


@router.get("/sessions", response_model=List[SessionListItem])
async def list_sessions(
    request: Request,
    user_id: Optional[str] = Query(default=None),
) -> List[SessionListItem]:
    """Retrieve list of conversation sessions for current user."""
    session_service = request.app.state.session_service
    return session_service.list_sessions(user_id=user_id)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    request: Request,
    user_id: Optional[str] = Query(default=None),
) -> SessionResponse:
    """Retrieve session metadata by session ID."""
    session_service = request.app.state.session_service
    session = await session_service.get_session(session_id=session_id, user_id=user_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return session
