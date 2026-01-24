import json
from urllib.parse import parse_qs
from collections.abc import Mapping
from years.datastructers import Hearders, QueryParams, URL, Cookie


class ClientDisconnect(Exception):
    """客户端断开连接异常"""


class State:
    """用户自己设置的状态"""


class Request(Mapping):
    def __init__(self, scope, receive=None):
        self._scope = scope
        self._receive = receive
        self.customed = False

    def __getitem__(self, key):
        return self._scope[key]

    def __iter__(self):
        return iter(self._scope)

    def __len__(self):
        return len(self._scope)

    @property
    def method(self):
        return self["method"]

    @property
    def state(self):
        if "state" not in self._scope:
            self._scope["state"] = State()

        return self._scope["state"]

    @property
    def url(self) -> URL:
        if not hasattr(self, "_url"):
            self._url = URL(self._scope)

        return self._url

    @property
    def cookies(self):
        if not hasattr(self, "_cookies"):
            self._cookies = Cookie(self.headers.get("cookie"))

        return self._cookies

    @property
    def query_params(self):
        if not hasattr(self, "_query_params"):
            self._query_params = QueryParams(self._scope["query_string"])
        return self._query_params

    @property
    def headers(self):
        if not hasattr(self, "_headers"):
            self._headers = Hearders(self._scope["headers"])
        return self._headers

    @property
    def path_params(self):
        return self._scope["path_params"]

    async def stream(self):
        if hasattr(self, "_body"):
            yield self._body
            return

        if self.customed:
            raise RuntimeError("该请求体的数据已被消费")

        if not self._receive:
            raise RuntimeError("请求体接受通道未传入")

        self.customed = True

        while True:
            current = await self._receive()
            if current["type"] == "http.request":
                yield current["body"]
                if not current["more_body"]:
                    break

            if current["type"] == "http.disconnect":
                raise ClientDisconnect()

    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            _body = b""
            async for chunk in self.stream():
                _body += chunk

            self._body = _body
        return self._body

    async def form(self):
        raw_data = await self.body()
        data = parse_qs(raw_data)
        return {k.decode(): v[-1].decode() for k, v in data.items()}

    async def json(self):
        raw_data = await self.body()
        return json.loads(raw_data)
