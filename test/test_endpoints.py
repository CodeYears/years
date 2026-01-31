import pytest

from years.endpoints import HTTPEndpoint
from years.responses import PlainTextResponse
from years.routing import Route, Router
from years.testclient import TestClient
from years.requests import Request


class Homepage(HTTPEndpoint):
    async def get(self, request: Request):
        username = request.path_params.get("username")
        if username is None:
            return PlainTextResponse("Hello, world!")
        return PlainTextResponse(f"Hello, {username}!")


app = Router(
    routes=[Route("/", endpoint=Homepage), Route("/{username}", endpoint=Homepage)]
)

client = TestClient(app)


@pytest.mark.asyncio
async def test_http_endpoint_route():
    response = await client.get("/")
    assert response.status_code == 200
    assert response.text == "Hello, world!"


@pytest.mark.asyncio
async def test_http_endpoint_route_path_params():
    response = await client.get("/tomchristie")
    assert response.status_code == 200
    assert response.text == "Hello, tomchristie!"


@pytest.mark.asyncio
async def test_http_endpoint_route_method():
    response = await client.post("/")
    assert response.status_code == 405
    assert response.text == "方法不匹配"
