import pytest
import asyncio

from years.testclient import TestClient
from years.responses import Response, StreamingResponse
from years.background import BackgroundTask


@pytest.mark.asyncio
async def test_text_response():
    async def app(scope, receive, send):
        response = Response("hello, world", media_type="text/plain")
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/")
    assert response.text == "hello, world"


@pytest.mark.asyncio
async def test_bytes_response():
    async def app(scope, receive, send):
        response = Response(b"xxxxx", media_type="image/png")
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/")
    assert response.content == b"xxxxx"


@pytest.mark.asyncio
async def test_streaming_response():
    filled_by_bg_task = ""

    async def app(scope, receive, send):
        async def numbers(minimum, maximum):
            for i in range(minimum, maximum + 1):
                yield str(i)
                if i != maximum:
                    yield ", "
                await asyncio.sleep(0)

        async def numbers_for_cleanup(start=1, stop=5):
            nonlocal filled_by_bg_task
            async for thing in numbers(start, stop):
                filled_by_bg_task = filled_by_bg_task + thing

        cleanup_task = BackgroundTask(numbers_for_cleanup, start=6, stop=9)
        generator = numbers(1, 5)
        response = StreamingResponse(
            generator, media_type="text/plain", background=cleanup_task
        )
        await response(scope, receive, send)

    assert filled_by_bg_task == ""
    client = TestClient(app)
    response = await client.get("/")
    assert response.text == "1, 2, 3, 4, 5"
    assert filled_by_bg_task == "6, 7, 8, 9"


@pytest.mark.asyncio
async def test_sync_streaming_response():
    async def app(scope, receive, send):
        async def numbers(minimum, maximum):
            for i in range(minimum, maximum + 1):
                yield str(i)
                if i != maximum:
                    yield ", "

        generator = numbers(1, 5)
        response = StreamingResponse(generator, media_type="text/plain")
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/")
    assert response.text == "1, 2, 3, 4, 5"
