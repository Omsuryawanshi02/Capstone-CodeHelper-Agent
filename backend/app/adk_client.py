"""Asynchronous client for communicating with the Google ADK API Server.

Connects to the official ADK API endpoints:
- GET /health
- GET /list-apps
- POST /apps/{app_name}/users/{user_id}/sessions
- GET /apps/{app_name}/users/{user_id}/sessions/{session_id}
- POST /run_sse
- POST /run
"""

import json
import logging
from typing import AsyncIterator, Dict, Any, Optional, List
import httpx

from .config import ADK_API_BASE_URL, ADK_APP_NAME, ADK_DEFAULT_USER_ID, REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class ADKClient:
    """Client for Google ADK API server interactions."""

    def __init__(
        self,
        base_url: str = ADK_API_BASE_URL,
        app_name: str = ADK_APP_NAME,
        default_user_id: str = ADK_DEFAULT_USER_ID,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ):
        self.base_url = base_url.rstrip("/")
        self.app_name = app_name
        self.default_user_id = default_user_id
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or initialize the underlying httpx.AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=5.0),
            )
        return self._client

    async def close(self):
        """Close the HTTP client cleanly."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def check_health(self) -> bool:
        """Check if the ADK API server is reachable and reports healthy."""
        try:
            client = await self.get_client()
            response = await client.get("/health", timeout=3.0)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"ADK health check failed: {e}")
            return False

    async def list_apps(self) -> List[str]:
        """List registered applications on the ADK server."""
        try:
            client = await self.get_client()
            response = await client.get("/list-apps", timeout=3.0)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.debug(f"ADK list_apps failed: {e}")
            return []

    async def create_session(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new conversation session via ADK API."""
        uid = user_id or self.default_user_id
        url = f"/apps/{self.app_name}/users/{uid}/sessions"
        payload = {}
        if session_id:
            payload["sessionId"] = session_id

        client = await self.get_client()
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def get_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve existing session metadata from ADK API."""
        uid = user_id or self.default_user_id
        url = f"/apps/{self.app_name}/users/{uid}/sessions/{session_id}"
        client = await self.get_client()
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        return None

    async def stream_agent_execution(
        self,
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Call ADK /run_sse endpoint and yield parsed JSON events."""
        uid = user_id or self.default_user_id
        url = f"{self.base_url}/run_sse"
        payload = {
            "app_name": self.app_name,
            "user_id": uid,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}],
            },
            "streaming": True,
        }

        # Dedicated client for streaming to avoid stream interruptions
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=5.0)) as stream_client:
            async with stream_client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    error_detail = body.decode(errors="replace")
                    raise RuntimeError(
                        f"ADK /run_sse failed with status {response.status_code}: {error_detail}"
                    )

                buffer = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        json_str = line[6:].strip()
                        if not json_str:
                            continue
                        try:
                            parsed_event = json.loads(json_str)
                            yield parsed_event
                        except json.JSONDecodeError as err:
                            logger.warning(f"Failed to decode ADK SSE event: {err}; line: {line}")

    async def run_agent_sync(
        self,
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Synchronously execute agent through ADK /run."""
        uid = user_id or self.default_user_id
        url = "/run"
        payload = {
            "app_name": self.app_name,
            "user_id": uid,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}],
            },
            "streaming": False,
        }

        client = await self.get_client()
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
