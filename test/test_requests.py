import pytest

from years import Request, JSONResponse
from years.testclient import TestClient
from years.requests import ClientDisconnect
from years.responses import Response


@pytest.mark.asyncio
async def test_request_url():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        data = {"method": request.method, "url": str(request.url)}
        response = JSONResponse(data)
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/123?a=abc")
    assert response.json() == {
        "method": "GET",
        "url": "http://testserver/123?a=abc",
    }

    response = await client.get("https://example.org:123/")
    assert response.json() == {"method": "GET", "url": "https://example.org:123/"}


@pytest.mark.asyncio
async def test_request_query_params():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        params = dict(request.query_params)
        response = JSONResponse({"params": params})
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/?a=123&b=456")
    assert response.json() == {"params": {"a": "123", "b": "456"}}


@pytest.mark.asyncio
async def test_request_headers():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        response = JSONResponse({"headers": dict(request.headers)})
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/", headers={"host": "example.org"})
    assert response.json() == {
        "headers": {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "connection": "keep-alive",
            "user-agent": "python-httpx/0.28.1",
            "host": "example.org",
        }
    }


@pytest.mark.asyncio
async def test_request_body():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        body = await request.body()
        response = JSONResponse({"body": body.decode()})
        await response(scope, receive, send)

    client = TestClient(app)

    response = await client.get("/")
    assert response.json() == {"body": ""}

    response = await client.post("/", json={"a": "123"})
    assert response.json() == {"body": '{"a":"123"}'}

    response = await client.post("/", content="abc")
    assert response.json() == {"body": "abc"}


@pytest.mark.asyncio
async def test_request_stream():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        body = b""
        async for chunk in request.stream():
            body += chunk
        response = JSONResponse({"body": body.decode()})
        await response(scope, receive, send)

    client = TestClient(app)

    response = await client.get("/")
    assert response.json() == {"body": ""}

    response = await client.post("/", json={"a": "123"})
    assert response.json() == {"body": '{"a":"123"}'}

    response = await client.post("/", content="abc")
    assert response.json() == {"body": "abc"}


@pytest.mark.asyncio
async def test_request_form_urlencoded():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        form = await request.form()
        response = JSONResponse({"form": dict(form)})
        await response(scope, receive, send)

    client = TestClient(app)

    response = await client.post("/", data={"abc": "123 @"})
    assert response.json() == {"form": {"abc": "123 @"}}


@pytest.mark.asyncio
async def test_request_body_then_stream():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        body = await request.body()
        chunks = b""
        async for chunk in request.stream():
            chunks += chunk
        response = JSONResponse({"body": body.decode(), "stream": chunks.decode()})
        await response(scope, receive, send)

    client = TestClient(app)

    response = await client.post("/", content="abc")
    assert response.json() == {"body": "abc", "stream": "abc"}


@pytest.mark.asyncio
async def test_request_json():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        data = await request.json()
        response = JSONResponse({"json": data})
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.post("/", json={"a": "123"})
    assert response.json() == {"json": {"a": "123"}}


def test_request_scope_interface():
    """
    A Request can be instantiated with a scope, and presents a `Mapping`
    interface.
    """
    request = Request({"type": "http", "method": "GET", "path": "/abc/"})
    assert request["method"] == "GET"
    assert dict(request) == {"type": "http", "method": "GET", "path": "/abc/"}
    assert len(request) == 3


@pytest.mark.asyncio
async def test_request_without_setting_receive():
    """
    If Request is instantiated without the receive channel, then .body()
    is not available.
    """

    async def app(scope, receive, send):
        request = Request(scope)
        try:
            data = await request.json()
        except RuntimeError:
            data = "Receive channel not available"
        response = JSONResponse({"json": data})
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.post("/", json={"a": "123"})
    assert response.json() == {"json": "Receive channel not available"}


@pytest.mark.asyncio
async def test_request_disconnect():
    """
    If a client disconnect occurs while reading request body
    then ClientDisconnect should be raised.
    """

    async def app(scope, receive, send):
        request = Request(scope, receive)
        await request.body()

    async def receiver():
        return {"type": "http.disconnect"}

    scope = {"type": "http", "method": "POST", "path": "/"}
    with pytest.raises(ClientDisconnect):
        await app(scope, receiver, None)


@pytest.mark.asyncio
async def test_request_state():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        request.state.example = 123
        response = JSONResponse({"state.example": request["state"].example})
        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/123?a=abc")
    assert response.json() == {"state.example": 123}


@pytest.mark.asyncio
async def test_request_cookies():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        mycookie = request.cookies.get("mycookie")
        if mycookie:
            response = Response(mycookie, media_type="text/plain")
        else:
            response = Response("Hello, world!", media_type="text/plain")
            response.set_cookie("mycookie", "Hello, cookies!")

        await response(scope, receive, send)

    client = TestClient(app)
    response = await client.get("/")
    assert response.text == "Hello, world!"
    response = await client.get("/")
    assert response.text == "Hello, cookies!"


@pytest.mark.asyncio
async def test_chunked_encoding():
    async def app(scope, receive, send):
        request = Request(scope, receive)
        body = await request.body()
        response = JSONResponse({"body": body.decode()})
        await response(scope, receive, send)

    client = TestClient(app)

    async def post_body():
        yield b"foo"
        yield "bar"

    response = await client.post("/", content=post_body())

    assert response.status_code == 200
    assert response.json() == {"body": "foobar"}
