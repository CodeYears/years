from __future__ import annotations
import traceback
from typing import Callable

from years.responses import PlainTextResponse, JSONResponse
from years.requests import Request


async def default_handlers(request: Request, exc: HTTPException):
    return JSONResponse(f"异常状态码: {exc.status_code}，异常内容: {exc.msg}")


class HTTPException(Exception):
    def __init__(self, status_code: int, msg: str):
        self.status_code = status_code
        self.msg = msg
        super().__init__(f"{self.status_code}: {msg}")


class ExceptionMiddleware:
    def __init__(self, endpoint: Callable, exception_handlers: dict):
        self.endpoint = endpoint
        self.exception_handlers = exception_handlers
        self.default_handler = default_handlers

    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)
        try:
            await self.endpoint(scope, receive, send)
        except HTTPException as e:
            if e.status_code in self.exception_handlers:
                response = await self.exception_handlers[e.status_code](request, e)
            else:
                response = await self.default_handler(request, e)
            await response(scope, send)
        except Exception:
            err_stack = traceback.format_exc()
            response = PlainTextResponse(err_stack)
            await response(scope, send)
