import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.v1.events import publish_event


@pytest.mark.asyncio
async def test_sse_heartbeat_and_event():
    """
    Verify that:
    1. The SSE endpoint streams a 'connected' event immediately.
    2. A published event is received by the subscriber.
    3. The 'completed' event closes the stream cleanly.
    """
    competition_id = "test-sse-comp-001"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Open SSE stream in background
        collected: list[str] = []

        async def stream_reader():
            async with client.stream("GET", f"/api/v1/events/{competition_id}") as resp:
                assert resp.status_code == 200
                assert "text/event-stream" in resp.headers["content-type"]
                saw_completed_event = False
                async for line in resp.aiter_lines():
                    if line:
                        collected.append(line)
                        if line == "event: completed":
                            saw_completed_event = True
                        elif saw_completed_event and line.startswith("data:"):
                            break  # data for completed received — done
                    if len(collected) > 30:
                        break

        async def publisher():
            await asyncio.sleep(0.1)  # Let the reader connect first
            publish_event(competition_id, "stage_start", {"stage": 1, "name": "Document Analysis"})
            await asyncio.sleep(0.05)
            publish_event(competition_id, "stage_done", {"stage": 1, "name": "Document Analysis"})
            await asyncio.sleep(0.05)
            publish_event(competition_id, "completed", {"problem_type": "Regression", "target": "sales"})

        await asyncio.gather(
            asyncio.wait_for(stream_reader(), timeout=5.0),
            publisher(),
        )

    raw = "\n".join(collected)
    assert "event: connected" in raw
    assert "event: stage_start" in raw
    assert "event: completed" in raw
    assert "Regression" in raw
