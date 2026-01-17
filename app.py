import asyncio
from contextlib import asynccontextmanager
from years.responses import (
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
    StreamingResponse,
    FileResponse,
)
from years.requests import Request
from years.endpoint import Endpoint
from years.background import BackgroundTask
from years import Years
from years.exceptions import HTTPException


@asynccontextmanager
async def lifespan():
    print("收到 startup 事件，数据库启动...")
    yield
    print("收到 shutdown 事件，清理工作开始...")


async def not_found(request: Request, exc: HTTPException):
    return HTMLResponse(content="路径找不到", status_code=exc.status_code)


async def method_not_matched(request: Request, exc: HTTPException):
    return HTMLResponse(content="方法不匹配", status_code=exc.status_code)


exception_handlers = {404: not_found, 405: method_not_matched}


sub = Years(debug=True, exception_handlers=exception_handlers)


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


@sub.get("/debug")
async def debug(request: Request):
    result = 1 / 0
    return PlainTextResponse(result)


@sub.classview("/class_view")
class ClassView(Endpoint):
    async def get(self, request: Request):
        return PlainTextResponse("Hello, Get!")

    async def post(self, request: Request):
        return PlainTextResponse("Hello, Post!")


def send_email(email: str):
    print(f"[Background Task: {email} 邮件发送中]")


@sub.get("/background_task")
async def background_task(request: Request):
    background_task = BackgroundTask(send_email, "123@gmail.com")
    return PlainTextResponse("Response complete!", background_task=background_task)


app = Years(lifespan=lifespan, debug=True)

app.mount("/sub/{name}", sub)
app.debug = False


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
