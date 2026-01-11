import asyncio
from years.responses import (
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
    StreamingResponse,
    FileResponse,
)
from years.requests import Request

from years import Years


sub = Years()


@sub.route("/html", methods=["GET", "POST"])
async def html(request):
    return HTMLResponse("<html><body><h1>Hello, World!</h1></body></html>")


@sub.get("/plaintext")
async def plaintext(request):
    return PlainTextResponse("Hello, World!")


@sub.get("/json")
async def json(request):
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
async def file(request):
    return FileResponse(
        "statics/1.JPG", media_type="image/jpeg", filename="download.jpg"
    )


@sub.get("/{username}/{id}/query")
def param(request: Request):
    username = request.path_params["username"]
    id = request.path_params["id"]
    return PlainTextResponse(f"姓名: {username}，学号: {id}")


@sub.get("/request")
def request(request):
    type = request["type"]
    method = request.method
    return JSONResponse(dict(type=type, method=method))


@sub.get("/request2")
async def request2(request: Request):
    """验证 Headers 是否正常"""
    return JSONResponse(request.headers)


@sub.get("/request3")
async def request3(request: Request):
    """验证查询参数是否正常解析"""
    return JSONResponse(request.query_params)


@sub.get("/request4/{name}/{id}")
async def request4(request: Request):
    host, port = request.url.host, request.url.port
    path = request.url.path
    return JSONResponse(dict(host=host, port=port, path=path))


@sub.post("/read_file")
async def read_file(request: Request):
    return StreamingResponse(request.stream(), media_type="text/html")


app = Years()

app.mount("/sub/{name}", sub)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
