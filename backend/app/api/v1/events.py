"""
Server-Sent Events (SSE) endpoint for real-time pipeline status streaming.
Uses an in-process asyncio.Queue per competition so the analysis worker can
push events that are immediately streamed to the connected browser.
"""
import asyncio
import json
from typing import AsyncGenerator
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/events", tags=["SSE"])

# In-process event bus: competition_id -> list of subscriber queues
_subscribers: dict[str, list[asyncio.Queue]] = {}


def publish_event(competition_id: str, event_type: str, data: dict) -> None:
    """
    Called by background workers to push a progress event.
    Thread-safe via asyncio — must only be called from the event loop.
    """
    payload = {
        "event": event_type,
        "competition_id": competition_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    for queue in _subscribers.get(competition_id, []):
        queue.put_nowait(payload)


async def _event_generator(
    request: Request,
    competition_id: str,
) -> AsyncGenerator[str, None]:
    """Yields SSE-formatted strings until the client disconnects."""
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(competition_id, []).append(queue)

    # Send initial connection event
    yield _sse_format("connected", {"competition_id": competition_id, "message": "Stream connected."})

    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=25.0)
                yield _sse_format(payload["event"], payload["data"])

                # Terminal events close the stream cleanly
                if payload["event"] in ("completed", "failed"):
                    break
            except asyncio.TimeoutError:
                # Heartbeat to keep the connection alive
                yield _sse_format("heartbeat", {"ts": datetime.now(timezone.utc).isoformat()})
    finally:
        queues = _subscribers.get(competition_id, [])
        if queue in queues:
            queues.remove(queue)


def _sse_format(event: str, data: dict) -> str:
    """Format a dict as a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.get("/{competition_id}")
async def competition_event_stream(competition_id: str, request: Request):
    """
    Stream pipeline progress events for a competition via SSE.
    Connect with: EventSource('/api/v1/events/{competition_id}')
    """
    return StreamingResponse(
        _event_generator(request, competition_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
