import traceback
from typing import Callable

from years.responses import PlainTextResponse


class DebugMiddleware:
    def __init__(self, endpoint: Callable):
        self.endpoint = endpoint

    async def __call__(self, scope, receive, send):
        try:
            await self.endpoint(scope, receive, send)
        except Exception:
            # 当出现异常的时候，根本没法到原来 return 的地方，原来的路直接断掉了
            # 所以只能在这里将响应 send 出去了
            err_stack = traceback.format_exc()
            response = PlainTextResponse(err_stack)
            await response(scope, send)
