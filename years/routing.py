import re
import enum
import typing
import asyncio
import inspect

from years.requests import Request
from years.exceptions import HTTPException


def request_response(endpoint: typing.Callable):
    async def wrapper(scope, receive, send):
        is_async = inspect.iscoroutinefunction(endpoint) or (
            not inspect.isclass(endpoint)
            and inspect.iscoroutinefunction(getattr(endpoint, "__call__", None))
        )
        request = Request(scope, receive)

        if is_async:
            response = await endpoint(request)
        else:
            response = await asyncio.to_thread(endpoint, request)

        await response(scope, send)

    return wrapper


class Mathched(enum.Enum):
    NONE = 0
    PARTICAL = 1
    FULL = 2


class BaseRoute:
    def matches(self, scope):
        raise NotImplementedError()

    async def __call__(self, scope, receive, send):
        raise NotImplementedError()


class Route(BaseRoute):
    def __init__(
        self, path: str, endpoint: typing.Callable, *, methods: list[str] = None
    ):
        self.path = path
        if not methods:
            self.methods = ["GET"]
        else:
            self.methods = methods
        self.endpoint = request_response(endpoint)

        if not path.endswith("/"):
            path += "/"

        if not path.startswith("/"):
            path = "/" + path

        self.regex = path.replace("{", "(?P<").replace("}", ">[^/]+)")

    def matches(self, scope: dict):
        path: str = scope["path"]

        if not path.endswith("/"):
            path += "/"

        if not path.startswith("/"):
            path = "/" + path

        res = re.fullmatch(self.regex, path)
        if res:
            if scope["method"] in self.methods:
                if "path_params" not in scope:
                    scope["path_params"] = {}
                scope["path_params"].update(res.groupdict())
                return Mathched.FULL, scope
            else:
                if "path_params" not in scope:
                    scope["path_params"] = {}
                scope["path_params"].update(res.groupdict())
                return Mathched.PARTICAL, scope

        return Mathched.NONE, {}

    async def __call__(self, scope, receive, send):
        await self.endpoint(scope, receive, send)


class Mount(BaseRoute):
    def __init__(
        self, path: str, routes: list[Route] = None, app: typing.Callable = None
    ):
        assert not (routes and app), "app 和 路径列表不可以同时存在的"
        self.router = Router(routes)
        self.app = app
        if not path.endswith("/"):
            path += "/"

        if not path.startswith("/"):
            path = "/" + path

        self.regex = "^" + path.replace("{", "(?P<").replace("}", ">[^/]+)")

    def matches(self, scope: dict):
        path: str = scope["path"]

        if not path.endswith("/"):
            path += "/"

        if not path.startswith("/"):
            path = "/" + path

        res = re.match(self.regex, path)
        if res:
            scope["path"] = path[res.span()[-1] :]  # noqa
            return Mathched.FULL, scope
        else:
            return Mathched.PARTICAL, scope

    async def __call__(self, scope, receive, send):
        if self.app:
            await self.app(scope, receive, send)
        else:
            await self.router(scope, receive, send)


class Router:
    def __init__(self, routes: list[Route] = None):
        self.routes = routes or []
        self.partical = False

    def add_route(self, route: Route):
        self.routes.append(route)

    def add_mount(self, mount: Mount):
        self.routes.append(mount)

    async def __call__(self, scope, receive, send):
        for route in self.routes:
            ret, new_scope = route.matches(scope)

            if ret is Mathched.FULL:
                await route(new_scope, receive, send)
                break

            if ret is Mathched.PARTICAL:
                self.partical = True

        else:
            if self.partical:
                raise HTTPException(405, "方法不匹配")
            else:
                raise HTTPException(404, "路径找不到")
