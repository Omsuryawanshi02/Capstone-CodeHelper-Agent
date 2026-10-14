"""Unit tests for EventAdapter: verifying normalization of ADK events into the frontend contract."""

import pytest
from backend.app.event_adapter import EventAdapter
from backend.app.schemas import NormalizedSSEEvent


class TestEventAdapter:
    """Tests for EventAdapter parsing and normalization."""

    def test_author_triggers_agent_activity(self):
        adapter = EventAdapter(session_id="test-session-1")
        raw_event = {"author": "code_searcher"}

        events = adapter.process_raw_adk_event(raw_event)
        assert len(events) == 1
        assert events[0].type == "agent_activity"
        assert events[0].agent_name == "code_searcher"
        assert "Pinecone" in events[0].activity

    def test_tool_call_activity_and_source_extraction(self):
        adapter = EventAdapter(session_id="test-session-2")
        raw_event = {
            "author": "code_explainer",
            "content": {
                "parts": [
                    {
                        "functionCall": {
                            "name": "read_project_file",
                            "args": {"file_path": "indexer.py"},
                        }
                    }
                ]
            },
        }

        events = adapter.process_raw_adk_event(raw_event)
        types = [e.type for e in events]
        assert "agent_activity" in types
        assert "source" in types

        source_event = next(e for e in events if e.type == "source")
        assert source_event.file_path == "indexer.py"

    def test_rag_result_source_extraction(self):
        adapter = EventAdapter(session_id="test-session-3")
        rag_text = (
            "Score: 0.8920 | File: target_project/config.py | Lines: 1-45\n"
            "  import os\n  def get_config(): return {}\n"
        )
        raw_event = {
            "content": {
                "parts": [
                    {
                        "functionResponse": {
                            "name": "rag_search",
                            "response": {"output": rag_text},
                        }
                    }
                ]
            }
        }

        events = adapter.process_raw_adk_event(raw_event)
        assert len(events) == 1
        assert events[0].type == "source"
        assert events[0].file_path == "target_project/config.py"
        assert events[0].start_line == 1
        assert events[0].end_line == 45
        assert events[0].score == 0.8920

    def test_token_streaming_and_turn_completion(self):
        adapter = EventAdapter(session_id="test-session-4")

        # First partial event
        chunk1 = {
            "partial": True,
            "content": {"parts": [{"text": "Hello "}]},
        }
        events1 = adapter.process_raw_adk_event(chunk1)
        assert len(events1) == 1
        assert events1[0].type == "token"
        assert events1[0].text == "Hello "

        # Second partial event
        chunk2 = {
            "partial": True,
            "content": {"parts": [{"text": "world!"}]},
        }
        events2 = adapter.process_raw_adk_event(chunk2)
        assert len(events2) == 1
        assert events2[0].type == "token"
        assert events2[0].text == "world!"

        # Turn complete event
        complete_event = {
            "turn_complete": True,
            "content": {"parts": []},
        }
        events3 = adapter.process_raw_adk_event(complete_event)
        types3 = [e.type for e in events3]
        assert "message" in types3
        assert "done" in types3

        message_event = next(e for e in events3 if e.type == "message")
        assert message_event.text == "Hello world!"

    def test_error_sanitization(self):
        adapter = EventAdapter(session_id="test-session-5")
        raw_error = {
            "errorMessage": "Upstream error with nvapi-secretkey1234567890abcdef at https://api.nvidia.com"
        }

        events = adapter.process_raw_adk_event(raw_error)
        assert len(events) == 1
        assert events[0].type == "error"
        assert "nvapi-secretkey" not in events[0].error
        assert "[REDACTED_KEY]" in events[0].error
