import pytest

from years import Request, JSONResponse
from years.testclient import TestClient


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
