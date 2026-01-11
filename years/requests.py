from collections.abc import Mapping
from years.datastructers import Hearders, QueryParams, URL


class Request(Mapping):
    def __init__(self, scope, receive):
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
    def url(self) -> URL:
        if not hasattr(self, "_url"):
            url = URL(self._scope)
            self._url = url

        return self._url

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
        if self.customed:
            raise RuntimeError("该请求体的数据已被消费")

        while True:
            current = await self._receive()
            yield current["body"]
            if not current["more_body"]:
                break
