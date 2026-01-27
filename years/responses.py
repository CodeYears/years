import json
import hashlib
import aiofiles

from years.datastructers import Hearders


class Response:
    media_type = None

    def __init__(
        self,
        content: str,
        status_code: int = 200,
        media_type: str = None,
        background=None,
    ):
        self.status_code = status_code
        self.content = content
        if media_type:
            self.media_type = media_type
        self.background = background

        # 实例化 headers 要放到上面，因为 init_headers 方法有可能会被重载
        self.headers = Hearders()
        self.init_headers()

    def init_headers(self):
        if self.media_type:
            self.headers["Content-Type"] = f"{self.media_type}; charset=utf-8"

    def set_cookie(self, key, value):
        self.headers.raw_headers["Set-Cookie"].append(f"{key}={value}")

    async def __call__(self, scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.headers.get_list(),
            }
        )

        if isinstance(self.content, bytes):
            body = self.content
        else:
            body = self.content.encode("utf-8")

        await send({"type": "http.response.body", "body": body})
        if self.background:
            await self.background()


class HTMLResponse(Response):
    media_type = "text/html"


class PlainTextResponse(Response):
    media_type = "text/plain"


class JSONResponse(Response):
    media_type = "application/json"

    async def __call__(self, scope, receive, send):
        self.content = json.dumps(dict(self.content), ensure_ascii=False)
        return await super().__call__(scope, receive, send)


class StreamingResponse(Response):
    def __init__(
        self, streamio, status_code: int = 200, media_type=None, background=None
    ):
        self.streamio = streamio
        self.status_code = status_code
        if media_type:
            self.media_type = media_type
        self.background = background
        self.headers = Hearders()
        self.init_headers()

    async def __call__(self, scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.headers.get_list(),
            }
        )

        # 你这里相当于用户只能传异步生成器，不可以传同步生成器的
        async for chunk in self.streamio:
            if isinstance(chunk, str):
                chunk = chunk.encode()

            await send(
                {
                    "type": "http.response.body",
                    "body": chunk,
                    "more_body": True,
                }
            )

        await send({"type": "http.response.body"})
        if self.background:
            await self.background()


class FileResponse(Response):
    def __init__(
        self,
        path: str,
        status_code: int = 200,
        media_type=None,
        filename: str = None,
        background=None,
    ):
        self.status_code = status_code
        self.path = path
        if media_type:
            self.media_type = media_type
        if filename:
            self.filename = filename
        self.background = background
        self.headers = Hearders()

    async def __call__(self, scope, receive, send):
        async with aiofiles.open(self.path, mode="rb") as fp:
            content = await fp.read()

            start = {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": [
                    [b"Content-Type", f"{self.media_type}".encode()],
                    [b"Content-Length", str(len(content)).encode()],
                    [b"ETag", hashlib.md5(content).hexdigest().encode()],
                ],
            }

            if hasattr(self, "filename"):
                start["headers"].append(
                    [
                        b"Content-Disposition",
                        f'attachment; filename="{self.filename}'.encode(),
                    ]
                )
            await send(start)

        await send({"type": "http.response.body", "body": content})
        if self.background:
            await self.background()
