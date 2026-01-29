import pytest

from years.responses import Response
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
