from years.routing import Router, Route, Mount


class Years:
    def __init__(self, router: Router = None):
        if router:
            self.router = router
        else:
            self.router = Router()

    def get(self, path: str):
        def decorate(endpoint):
            route = Route(path, endpoint, methods=["GET"])
            self.router.add_route(route)

        return decorate

    def mount(self, path, app):
        mount = Mount(path, app=app)
        self.router.add_mount(mount)

    async def __call__(self, scope, receive, send):
        await self.router(scope, receive, send)
