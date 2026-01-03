import asyncio
from years.responses import (
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
    StreamingResponse,
    FileResponse,
)

from years import Years


sub = Years()


@sub.get("/html")
async def html(scope, receive, send):
    response = HTMLResponse("<html><body><h1>Hello, World!</h1></body></html>")
    await response(scope, send)


@sub.get("/plaintext")
async def plaintext(scope, receive, send):
    response = PlainTextResponse("Hello, World!")
    await response(scope, send)


@sub.get("/json")
async def json(scope, receive, send):
    response = JSONResponse({"Hello": "World"})
    await response(scope, send)


async def slow_numbers(minimum, maximum):
    yield ("<html><body><ul>")
    for number in range(minimum, maximum + 1):
        yield "<li>%d</li>" % number
        await asyncio.sleep(0.5)
    yield ("</ul></body></html>")


@sub.get("/stream")
async def stream(scope, receive, send):
    generator = slow_numbers(1, 10)
    response = StreamingResponse(generator, media_type="text/html")
    await response(scope, send)


@sub.get("/file")
async def file(scope, receive, send):
    response = FileResponse(
        "statics/1.JPG", media_type="image/jpeg", filename="download.jpg"
    )
    await response(scope, send)


@sub.get("/{username}/{id}/query")
async def param(scope, receive, send):
    username = scope["username"]
    id = scope["id"]
    response = PlainTextResponse(f"姓名: {username}，学号: {id}")
    await response(scope, send)


app = Years()

app.mount("/sub/{name}", sub)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
