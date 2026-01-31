from years.requests import Request


class HTTPEndpoint:
    def get_methods(self):
        return ["GET", "POST"]

    async def __call__(self, request: Request):
        if request.method == "GET":
            return await self.get(request)

        if request.method == "POST":
            return await self.post(request)
