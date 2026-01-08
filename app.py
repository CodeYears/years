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
def html(request):
    return HTMLResponse("<html><body><h1>Hello, World!</h1></body></html>")


@sub.get("/plaintext")
def plaintext(request):
    return PlainTextResponse("Hello, World!")


@sub.get("/json")
def json(request):
    return JSONResponse({"Hello": "World"})


async def slow_numbers(minimum, maximum):
    yield ("<html><body><ul>")
    for number in range(minimum, maximum + 1):
        yield "<li>%d</li>" % number
        await asyncio.sleep(0.5)
    yield ("</ul></body></html>")


@sub.get("/stream")
def stream(request):
    generator = slow_numbers(1, 10)
    return StreamingResponse(generator, media_type="text/html")


@sub.get("/file")
def file(request):
    return FileResponse(
        "statics/1.JPG", media_type="image/jpeg", filename="download.jpg"
    )


# @sub.get("/{username}/{id}/query")
# async def param(scope, receive, send):
#     username = scope["username"]
#     id = scope["id"]
#     response = PlainTextResponse(f"姓名: {username}，学号: {id}")
#     await response(scope, send)


@sub.get("/request")
def request(request):
    type = request["type"]
    method = request.method
    return JSONResponse(dict(type=type, method=method))


app = Years()

app.mount("/sub/{name}", sub)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
