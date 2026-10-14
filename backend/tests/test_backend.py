"""Unit and integration tests for FastAPI backend routes, schemas, session isolation, and streaming."""

import json
from unittest.mock import AsyncMock, patch
import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.adk_client import ADKClient
from backend.app.session_service import SessionService


@pytest.fixture
def test_client():
    """Create test client with fresh mocked services."""
    mock_adk = AsyncMock(spec=ADKClient)
    mock_adk.base_url = "http://127.0.0.1:8000"
    mock_adk.app_name = "code_helper"
    mock_adk.default_user_id = "default_user"
    mock_adk.check_health.return_value = True
    mock_adk.create_session.return_value = {
        "id": "adk-session-123",
        "appName": "code_helper",
        "userId": "default_user",
    }
    mock_adk.get_session.return_value = {
        "id": "adk-session-123",
        "appName": "code_helper",
        "userId": "default_user",
    }

    session_service = SessionService(adk_client=mock_adk)

    app.state.adk_client = mock_adk
    app.state.session_service = session_service

    with TestClient(app) as client:
        yield client, mock_adk, session_service


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_success(self, test_client):
        client, mock_adk, _ = test_client
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["backend_running"] is True
        assert data["adk_reachable"] is True
        assert data["adk_app_name"] == "code_helper"
        assert "timestamp" in data
        # Ensure no secrets leak
        content = response.text
        assert "key" not in content.lower() or "configured" in content.lower()

    def test_health_adk_unreachable(self, test_client):
        client, mock_adk, _ = test_client
        mock_adk.check_health.return_value = False
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["adk_reachable"] is False
        assert data["status"] == "degraded"

    def test_cors_headers(self, test_client):
        client, _, _ = test_client
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


class TestSessionRoutes:
    """Tests for session management and isolation."""

    def test_create_session(self, test_client):
        client, mock_adk, _ = test_client
        response = client.post("/api/sessions", json={"title": "Test Chat"})
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "adk-session-123"
        assert data["app_name"] == "code_helper"
        assert data["title"] == "Test Chat"

    def test_session_isolation(self, test_client):
        client, mock_adk, session_service = test_client

        # Create session A
        mock_adk.create_session.return_value = {"id": "session-A", "appName": "code_helper"}
        resp_a = client.post("/api/sessions", json={"title": "Session A"})
        id_a = resp_a.json()["session_id"]

        # Create session B
        mock_adk.create_session.return_value = {"id": "session-B", "appName": "code_helper"}
        resp_b = client.post("/api/sessions", json={"title": "Session B"})
        id_b = resp_b.json()["session_id"]

        assert id_a != id_b

        # List sessions
        list_resp = client.get("/api/sessions")
        assert list_resp.status_code == 200
        sessions = list_resp.json()
        session_ids = [s["session_id"] for s in sessions]
        assert "session-A" in session_ids
        assert "session-B" in session_ids

    def test_get_nonexistent_session(self, test_client):
        client, mock_adk, _ = test_client
        mock_adk.get_session.return_value = None
        response = client.get("/api/sessions/unknown-id")
        assert response.status_code == 404


class TestChatValidationAndStreaming:
    """Tests for chat validation, streaming, and error handling."""

    def test_chat_validation_empty_message(self, test_client):
        client, _, _ = test_client
        response = client.post("/api/chat/stream", json={"session_id": "s1", "message": ""})
        assert response.status_code == 422

    def test_chat_validation_missing_session(self, test_client):
        client, _, _ = test_client
        response = client.post("/api/chat/stream", json={"message": "Where is config.py?"})
        assert response.status_code == 422

    def test_chat_streaming_success(self, test_client):
        client, mock_adk, session_service = test_client

        # Seed an existing session
        session_service._sessions["test-stream-session"] = {
            "session_id": "test-stream-session",
            "app_name": "code_helper",
            "user_id": "default_user",
            "title": "Stream Test",
            "created_at": 1000.0,
            "last_message_at": 1000.0,
            "message_count": 0,
        }

        # Mock stream generator
        async def mock_events(**kwargs):
            yield {"author": "coordinator"}
            yield {"author": "code_searcher"}
            yield {
                "partial": True,
                "content": {"parts": [{"text": "Found in config.py"}]},
            }
            yield {
                "turn_complete": True,
                "content": {"parts": []},
            }

        mock_adk.stream_agent_execution.side_effect = mock_events

        response = client.post(
            "/api/chat/stream",
            json={"session_id": "test-stream-session", "message": "Where is the config?"},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        # Parse SSE lines
        sse_lines = [
            line for line in response.text.split("\n")
            if line.startswith("data: ")
        ]
        parsed_events = [json.loads(line[6:]) for line in sse_lines]

        types = [e["type"] for e in parsed_events]
        assert "status" in types
        assert "agent_activity" in types
        assert "token" in types
        assert "message" in types
        assert "done" in types

        # Check in-session message count updated
        assert session_service._sessions["test-stream-session"]["message_count"] == 1

    def test_chat_streaming_upstream_error_handled(self, test_client):
        client, mock_adk, session_service = test_client

        # Mock stream generator that throws
        async def failing_stream(**kwargs):
            raise ConnectionResetError("ADK service connection dropped")
            yield {}

        mock_adk.stream_agent_execution.side_effect = failing_stream

        response = client.post(
            "/api/chat/stream",
            json={"session_id": "any-session", "message": "Help me run this"},
        )
        assert response.status_code == 200

        sse_lines = [
            line for line in response.text.split("\n")
            if line.startswith("data: ")
        ]
        parsed_events = [json.loads(line[6:]) for line in sse_lines]
        types = [e["type"] for e in parsed_events]

        assert "error" in types
        assert "done" in types
        err_event = next(e for e in parsed_events if e["type"] == "error")
        assert "connection dropped" in err_event["error"].lower()
