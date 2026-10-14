"""Chat endpoints supporting Server-Sent Events (SSE) and synchronous fallback."""

import json
import logging
from typing import AsyncIterator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..schemas import ChatMessageRequest, ChatMessageResponse, NormalizedSSEEvent, SourceMetadata
from ..event_adapter import EventAdapter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(req: ChatMessageRequest, request: Request) -> StreamingResponse:
    """Stream agent conversation events using Server-Sent Events (SSE)."""
    adk_client = request.app.state.adk_client
    session_service = request.app.state.session_service

    # Verify session or auto-register if valid string provided
    session = await session_service.get_session(session_id=req.session_id, user_id=req.user_id)
    if not session:
        # Check if ADK service can resolve or accept it
        try:
            session = await session_service.create_session(
                title=req.message[:30], user_id=req.user_id
            )
            # Reassign session_id to backend-generated session if missing
            req.session_id = session.session_id
        except Exception as e:
            logger.warning(f"Could not initialize session on-the-fly: {e}")

    # Track activity preview for recent chats
    session_service.record_activity(req.session_id, preview_text=req.message)

    adapter = EventAdapter(session_id=req.session_id)

    async def sse_event_generator() -> AsyncIterator[str]:
        # 1. Initial connection status
        initial_event = NormalizedSSEEvent(
            type="status",
            session_id=req.session_id,
            text="Query received. Initializing multi-agent reasoning...",
        )
        yield f"data: {initial_event.model_dump_json(exclude_none=True)}\n\n"

        try:
            # 2. Stream from Google ADK
            async for raw_adk_event in adk_client.stream_agent_execution(
                session_id=req.session_id,
                message=req.message,
                user_id=req.user_id,
            ):
                normalized_events = adapter.process_raw_adk_event(raw_adk_event)
                for event in normalized_events:
                    yield f"data: {event.model_dump_json(exclude_none=True)}\n\n"

            # 3. Ensure completion event is sent if turnComplete wasn't emitted explicitly
            if not adapter.turn_completed:
                if adapter.accumulated_text:
                    msg_event = NormalizedSSEEvent(
                        type="message",
                        session_id=req.session_id,
                        text=adapter.accumulated_text,
                        agent_name=adapter.current_agent,
                    )
                    yield f"data: {msg_event.model_dump_json(exclude_none=True)}\n\n"

                done_event = NormalizedSSEEvent(
                    type="done",
                    session_id=req.session_id,
                )
                yield f"data: {done_event.model_dump_json(exclude_none=True)}\n\n"

        except Exception as e:
            logger.error(f"Error streaming from ADK agent: {e}", exc_info=True)
            error_event = NormalizedSSEEvent(
                type="error",
                session_id=req.session_id,
                error=adapter._sanitize_error(f"Agent service error: {str(e)}"),
            )
            yield f"data: {error_event.model_dump_json(exclude_none=True)}\n\n"
            done_event = NormalizedSSEEvent(
                type="done",
                session_id=req.session_id,
            )
            yield f"data: {done_event.model_dump_json(exclude_none=True)}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat", response_model=ChatMessageResponse)
async def chat_sync(req: ChatMessageRequest, request: Request) -> ChatMessageResponse:
    """Non-streaming synchronous chat endpoint for debugging and fallback."""
    adk_client = request.app.state.adk_client
    session_service = request.app.state.session_service

    session_service.record_activity(req.session_id, preview_text=req.message)

    adapter = EventAdapter(session_id=req.session_id)
    try:
        raw_events = await adk_client.run_agent_sync(
            session_id=req.session_id,
            message=req.message,
            user_id=req.user_id,
        )
        for raw_event in raw_events:
            adapter.process_raw_adk_event(raw_event)

        # Build sources from adapter's emitted sources
        sources = [
            SourceMetadata(file_path=fpath, start_line=sline, end_line=eline)
            for fpath, sline, eline in adapter.emitted_sources
        ]

        return ChatMessageResponse(
            session_id=req.session_id,
            message=adapter.accumulated_text or "No response generated.",
            agent_name=adapter.current_agent,
            sources=sources,
        )
    except Exception as e:
        logger.error(f"Synchronous chat call failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=adapter._sanitize_error(f"Failed to communicate with ADK runtime: {e}"),
        )
