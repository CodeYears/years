import json
import hashlib
import aiofiles


class Response:
    media_type = None

    def __init__(self, content: str, status_code: int = 200, media_type: str = None):
        self.status_code = status_code
        self.content = content
        if media_type:
            self.media_type = media_type

    async def __call__(self, scope, send):
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": [
                    [b"Content-Type", f"{self.media_type}; charset=utf-8".encode()]
                ],
            }
        )

        await send({"type": "http.response.body", "body": self.content.encode("utf-8")})


class HTMLResponse(Response):
    media_type = "text/html"


class PlainTextResponse(Response):
    media_type = "text/plain"


class JSONResponse(Response):
    media_type = "application/json"

    async def __call__(self, scope, send):
        self.content = json.dumps(dict(self.content), ensure_ascii=False)
        return await super().__call__(scope, send)


class StreamingResponse(Response):
    def __init__(self, streamio, status_code: int = 200, media_type=None):
        self.streamio = streamio
        self.status_code = status_code
        if media_type:
            self.media_type = media_type

    async def __call__(self, scope, send):
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": [
                    [b"Content-Type", f"{self.media_type}; charset=utf-8".encode()]
                ],
            }
        )

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


class FileResponse(Response):
    def __init__(
        self, path: str, status_code: int = 200, media_type=None, filename: str = None
    ):
        self.status_code = status_code
        self.path = path
        if media_type:
            self.media_type = media_type

        if filename:
            self.filename = filename

    async def __call__(self, scope, send):
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
