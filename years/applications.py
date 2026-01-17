from contextlib import AsyncExitStack
from years.routing import Router, Route, Mount
from years.exceptions import ExceptionMiddleware
from years.endpoint import Endpoint


class Years:
    def __init__(
        self,
        router: Router = None,
        lifespan=None,
        debug: bool = False,
        exception_handlers: dict = None,
    ):
        self.debug = debug
        self.lifespan = lifespan
        if router:
            self.router = router
        else:
            self.router = Router()

        self.exception_handlers = exception_handlers or {}

    def route(self, path: str, methods=None):
        if methods is None:
            methods = ["GET"]

        def decorate(endpoint):
            route = Route(path, endpoint, methods=methods)
            self.router.add_route(route)

        return decorate

    def classview(self, path):
        def decorate(endpoint: Endpoint):
            endpoint = endpoint()
            route = Route(path, endpoint, methods=endpoint.get_methods())
            self.router.add_route(route)

        return decorate

    def get(self, path: str):
        def decorate(endpoint):
            route = Route(path, endpoint, methods=["GET"])
            self.router.add_route(route)

        return decorate

    def post(self, path: str):
        def decorate(endpoint):
            route = Route(path, endpoint, methods=["POST"])
            self.router.add_route(route)

        return decorate

    def mount(self, path, app):
        mount = Mount(path, app=app)
        self.router.add_mount(mount)

    async def run_lifespan(self, scope, receive, send):
        stack = AsyncExitStack()
        if self.lifespan is None:
            return

        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await stack.enter_async_context(self.lifespan())
                await send({"type": "lifespan.startup.complete"})

            elif message["type"] == "lifespan.shutdown":
                await stack.aclose()
                await send({"type": "lifespan.shutdown.complete"})
                return

    async def __call__(self, scope, receive, send):
        if self.debug:
            self.router = ExceptionMiddleware(self.router, self.exception_handlers)

        if scope["type"] == "lifespan":
            await self.run_lifespan(scope, receive, send)
        else:
            await self.router(scope, receive, send)
