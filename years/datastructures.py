from collections import defaultdict
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
            else:
                url += "/" if not url.endswith("/") else ""

        self._url = url

    def __str__(self):
        return self._url

    def __eq__(self, value):
        return value == self._url
        
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


class Hearders(MutableMapping):
    def __init__(self, headers: list | dict = None):
        """headers不止可以从 ASGI 框架传过来的列表构建
        也可以从字典接口构建"""
        self.raw_headers = self._init_headers(headers)

    def _init_headers(self, headers):
        raw_headers = defaultdict(list)

        if isinstance(headers, list):
            for key, value in headers:
                key, value = key.decode("latin-1").lower(), value.decode()
                raw_headers[key].append(value)

        elif isinstance(headers, dict):
            for key, value in headers.items():
                if isinstance(key, bytes):
                    key = key.decode("latin-1")

                raw_headers[key.lower()].append(value)

        return raw_headers

    def __len__(self):
        return len(self.raw_headers)

    def __getitem__(self, key):
        values = self.raw_headers[key]
        return values[-1] if values else None

    def __iter__(self):
        return iter(self.raw_headers)

    def __setitem__(self, key, value):
        self.raw_headers[key] = [value]

    def append(self, key, value):
        self.raw_headers[key].append(value)

    def __delitem__(self, key):
        del self.raw_headers[key]

    def get_last(self, key):
        values = self.get(key)
        return values[-1] if values else None

    def get_list(self):
        results = []
        for key, values in self.raw_headers.items():
            for value in values:
                results.append([key.encode(), value.encode()])

        return results


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
            self._cookie = {cookies.split("=")[0]: cookies.split("=")[1]}
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
