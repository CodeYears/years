import pytest

from years.responses import Response, PlainTextResponse
from years.routing import Router, Route, Mount
from years.testclient import TestClient


def homepage(request):
    return Response("Hello, world", media_type="text/plain")


def users(request):
    return Response("All users", media_type="text/plain")


def user(request):
    content = "User " + request.path_params["username"]
    return Response(content, media_type="text/plain")


def user_me(request):
    content = "User fixed me"
    return Response(content, media_type="text/plain")


def user_no_match(request):  # pragma: no cover
    content = "User fixed no match"
    return Response(content, media_type="text/plain")


app = Router(
    [
        Route("/", endpoint=homepage, methods=["GET"]),
        Mount(
            "/users",
            routes=[
                Route("/", endpoint=users),
                Route("/me", endpoint=user_me),
                Route("/{username}", endpoint=user),
                Route("/nomatch", endpoint=user_no_match),
            ],
        ),
        Mount("/static", app=Response("xxxxx", media_type="image/png")),
    ]
)


@app.route("/func")
def func_homepage(request):
    return Response("Hello, world!", media_type="text/plain")


@app.route("/func", methods=["POST"])
def contact(request):
    return Response("Hello, POST!", media_type="text/plain")


client = TestClient(app)


@pytest.mark.asyncio
async def test_router():
    response = await client.get("/")
    assert response.status_code == 200
    assert response.text == "Hello, world"

    response = await client.post("/")
    assert response.status_code == 405
    assert response.text == "方法不匹配"

    response = await client.get("/foo")
    assert response.status_code == 404
    assert response.text == "路径找不到"

    response = await client.get("/users")
    assert response.status_code == 200
    assert response.text == "All users"

    response = await client.get("/users/tomchristie")
    assert response.status_code == 200
    assert response.text == "User tomchristie"

    response = await client.get("/users/me")
    assert response.status_code == 200
    assert response.text == "User fixed me"

    response = await client.get("/users/nomatch")
    assert response.status_code == 200
    assert response.text == "User nomatch"

    response = await client.get("/static/123")
    assert response.status_code == 200
    assert response.text == "xxxxx"


@pytest.mark.asyncio
async def test_router_add_route():
    response = await client.get("/func")
    assert response.status_code == 200
    assert response.text == "Hello, world!"


@pytest.mark.asyncio
async def test_router_duplicate_path():
    response = await client.post("/func")
    assert response.status_code == 200
    assert response.text == "Hello, POST!"


ok = PlainTextResponse("OK")

@pytest.mark.asyncio
async def test_mount_urls():
    mounted = Router([Mount("/users", app=ok)])
    client = TestClient(mounted)
    response = await client.get("/users")
    assert response.status_code == 200
    response = await client.get("/users")

    # 为什么 response 里面还会有 url 呢？
    assert response.url == "http://testserver/users"
    assert (await client.get("/users/")).status_code == 200
    assert (await client.get("/users/a")).status_code == 200
    assert (await client.get("/usersa")).status_code == 404
