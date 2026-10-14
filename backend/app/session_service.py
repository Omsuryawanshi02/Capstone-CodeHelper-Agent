"""Session management service for coordinating user sessions between FastAPI and ADK."""

import time
import uuid
import logging
from typing import Dict, Any, Optional, List
from .schemas import SessionResponse, SessionListItem
from .adk_client import ADKClient

logger = logging.getLogger(__name__)


class SessionService:
    """Manages active conversation sessions and coordinates with the ADK runtime."""

    def __init__(self, adk_client: ADKClient):
        self.adk_client = adk_client
        # In-memory session registry (session_id -> metadata)
        self._sessions: Dict[str, Dict[str, Any]] = {}

    async def create_session(
        self,
        title: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> SessionResponse:
        """Create a session in ADK and register it locally."""
        uid = user_id or self.adk_client.default_user_id
        session_title = title or "New Conversation"

        try:
            # Create session in ADK API server
            adk_resp = await self.adk_client.create_session(user_id=uid)
            session_id = adk_resp.get("id") or str(uuid.uuid4())
            app_name = adk_resp.get("appName") or self.adk_client.app_name
        except Exception as e:
            logger.warning(f"ADK session creation call failed ({e}); generating local session identifier.")
            session_id = str(uuid.uuid4())
            app_name = self.adk_client.app_name

        now = time.time()
        record = {
            "session_id": session_id,
            "app_name": app_name,
            "user_id": uid,
            "title": session_title,
            "created_at": now,
            "last_message_at": now,
            "message_count": 0,
        }
        self._sessions[session_id] = record

        return SessionResponse(
            session_id=session_id,
            app_name=app_name,
            user_id=uid,
            title=session_title,
            created_at=now,
        )

    async def get_session(self, session_id: str, user_id: Optional[str] = None) -> Optional[SessionResponse]:
        """Verify session existence and return its metadata."""
        # Check local registry first
        if session_id in self._sessions:
            item = self._sessions[session_id]
            return SessionResponse(
                session_id=item["session_id"],
                app_name=item["app_name"],
                user_id=item["user_id"],
                title=item.get("title"),
                created_at=item["created_at"],
            )

        # Fallback to querying ADK server directly
        try:
            adk_data = await self.adk_client.get_session(session_id=session_id, user_id=user_id)
            if adk_data:
                now = time.time()
                record = {
                    "session_id": session_id,
                    "app_name": adk_data.get("appName", self.adk_client.app_name),
                    "user_id": adk_data.get("userId", user_id or self.adk_client.default_user_id),
                    "title": "Existing Session",
                    "created_at": now,
                    "last_message_at": now,
                    "message_count": len(adk_data.get("events", [])),
                }
                self._sessions[session_id] = record
                return SessionResponse(
                    session_id=session_id,
                    app_name=record["app_name"],
                    user_id=record["user_id"],
                    title=record["title"],
                    created_at=now,
                )
        except Exception as e:
            logger.debug(f"Could not retrieve session {session_id} from ADK: {e}")

        return None

    def list_sessions(self, user_id: Optional[str] = None) -> List[SessionListItem]:
        """List sessions registered for the user, sorted newest first."""
        uid = user_id or self.adk_client.default_user_id
        matching = [
            SessionListItem(
                session_id=s["session_id"],
                title=s.get("title") or "Conversation",
                created_at=s["created_at"],
                last_message_at=s.get("last_message_at"),
                message_count=s.get("message_count", 0),
            )
            for s in self._sessions.values()
            if s.get("user_id") == uid
        ]
        matching.sort(key=lambda x: x.last_message_at or x.created_at, reverse=True)
        return matching

    def record_activity(self, session_id: str, preview_text: Optional[str] = None):
        """Update last message timestamp and auto-generate title from first prompt if default."""
        if session_id in self._sessions:
            self._sessions[session_id]["last_message_at"] = time.time()
            self._sessions[session_id]["message_count"] = (
                self._sessions[session_id].get("message_count", 0) + 1
            )
            # If default title, use snippet of first message
            if preview_text and self._sessions[session_id].get("title") in ("New Conversation", None):
                clean_title = preview_text.strip().split("\n")[0]
                if len(clean_title) > 36:
                    clean_title = clean_title[:33] + "..."
                self._sessions[session_id]["title"] = clean_title
