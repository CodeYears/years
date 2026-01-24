from collections.abc import Mapping, MutableMapping
from urllib.parse import parse_qsl, unquote, urlparse


class URL:
    def __init__(self, scope=None, url=None):
        assert not (scope and url), "构建不可以同时提供 url 和 scope 参数"
        if scope is not None:
            host, port = scope["server"]
            scheme = scope["scheme"]
            path = unquote(scope["raw_path"])
            query_string = scope["query_string"].decode("utf-8")
            if port is not None:
                url = f"{scheme}://{host}:{port}{path}"
            else:
                url = f"{scheme}://{host}{path}"

            if query_string:
                url += "?" + query_string

        self._url = url

    def __str__(self):
        return self._url

    @property
    def components(self):
        if not hasattr(self, "_components"):
            components = urlparse(self._url)
            self._components = components
        return self._components

    @property
    def sheme(self):
        return self.components.scheme

    @property
    def host(self):
        return self.components.hostname

    @property
    def port(self):
        return self.components.port

    @property
    def username(self):
        return self.components.username

    @property
    def password(self):
        return self.components.password

    @property
    def path(self):
        return self.components.path

    @property
    def fragment(self):
        return self.components.fragment

    @property
    def netloc(self):
        return self.components.netloc


class Hearders(Mapping):
    def __init__(self, hearders: list):
        self._headers = hearders

    def __getitem__(self, key: str):
        for hearder_key, hearder_value in self._headers:
            if hearder_key.decode("latin-1").lower() == key.lower():
                return hearder_value.decode("latin-1").lower()
        raise KeyError(f"Headers 中不存在{key.lower()}")

    def __len__(self):
        return len(self._headers)

    def __iter__(self):
        for key, _ in self._headers:
            yield key.decode("latin-1")

    def dump(self):
        return dict(self)


class QueryParams(Mapping):
    """查询参数先弄成只接受一个参数的，后面再弄多值映射"""

    def __init__(self, query_params: str):
        d = dict(parse_qsl(query_params))
        self._query_params = {
            key.decode("latin-1"): value.decode("latin-1") for key, value in d.items()
        }

    def __getitem__(self, key):
        return self._query_params[key]

    def __len__(self):
        return len(self._query_params)

    def __iter__(self):
        return iter(self._query_params)


class Cookie(MutableMapping):
    def __init__(self, cookies: str = None):
        if cookies:
            self._cookie = {k: v for k, v in cookies.split(";")}
        else:
            self._cookie = {}

    def __iter__(self):
        return iter(self._cookie)

    def __len__(self):
        return len(self._cookie)

    def __getitem__(self, key):
        return self._cookie[key]

    def __setitem__(self, key, value):
        self._cookie[key] = value

    def __delitem__(self, key):
        del self._cookie[key]
