import os
import pytest
import asyncio

from years.testclient import TestClient
from years.responses import Response, StreamingResponse, FileResponse
from years.background import BackgroundTask
from years.requests import Request


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


@pytest.mark.asyncio
async def test_response_headers():
    async def app(scope, receive, send):
        headers = {"x-header-1": "123", "x-header-2": "456"}
        response = Response("hello, world", media_type="text/plain", headers=headers)
        response.headers["x-header-2"] = "789"
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/")
    assert response.headers["x-header-1"] == "123"
    assert response.headers["x-header-2"] == "789"


@pytest.mark.asyncio
async def test_file_response(tmpdir):
    path = os.path.join(tmpdir, "xyz")
    content = b"<file content>" * 1000
    with open(path, "wb") as file:
        file.write(content)

    filled_by_bg_task = ""

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

    async def app(scope, receive, send):
        response = FileResponse(
            path=path, filename="example.png", background=cleanup_task
        )
        await response(scope, receive, send)

    assert filled_by_bg_task == ""
    client = TestClient(app)
    response = await client.get("/")
    expected_disposition = 'attachment; filename="example.png"'
    assert response.status_code == 200
    assert response.content == content
    assert response.headers["content-type"] == "image/png"
    assert response.headers["content-disposition"] == expected_disposition
    assert "content-length" in response.headers
    assert "last-modified" in response.headers
    assert "etag" in response.headers
    assert filled_by_bg_task == "6, 7, 8, 9"


@pytest.mark.asyncio
async def test_file_response_with_directory_raises_error(tmpdir):
    app = FileResponse(path=tmpdir, filename="example.png")
    client = TestClient(app)
    with pytest.raises(RuntimeError) as exc:
        await client.get("/")
    assert "is not a file" in str(exc)


@pytest.mark.asyncio
async def test_file_response_with_missing_file_raises_error(tmpdir):
    path = os.path.join(tmpdir, "404.txt")
    app = FileResponse(path=path, filename="404.txt")
    client = TestClient(app)
    with pytest.raises(RuntimeError) as exc:
        await client.get("/")
    assert "does not exist" in str(exc)


@pytest.mark.asyncio
async def test_set_cookie():
    async def app(scope, receive, send):
        response = Response("Hello, world!", media_type="text/plain")
        response.set_cookie(
            "mycookie",
            "myvalue",
        )
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/")
    assert response.text == "Hello, world!"


@pytest.mark.asyncio
async def test_delete_cookie():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        response = Response("Hello, world!", media_type="text/plain")
        if request.cookies.get("mycookie"):
            response.delete_cookie("mycookie")
        else:
            response.set_cookie("mycookie", "myvalue")
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/")
    assert response.cookies["mycookie"]
    response = await client.get("/")
    assert not response.cookies.get("mycookie")


@pytest.mark.asyncio
async def test_populate_headers():
    app = Response(content="hi", headers={}, media_type="text/html")
    client = TestClient(app)
    response = await client.get("/")
    assert response.text == "hi"
    assert response.headers["content-length"] == "2"
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.asyncio
async def test_head_method():
    app = Response("hello, world", media_type="text/plain")
    client = TestClient(app)
    response = await client.head("/")
    assert response.text == ""
