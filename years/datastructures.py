import re
from copy import deepcopy
from collections import defaultdict
from collections.abc import Mapping, MutableMapping
from urllib.parse import parse_qs, unquote, urlparse, urlunparse


class URL:
    def __init__(self, url=None, scope: dict = None):
        assert not (scope and url), "构建不可以同时提供 url 和 scope 参数"
        if scope is not None:
            host, port = scope.get("server", ("", None))
            scheme = scope.get("scheme", "")
            path = unquote(scope.get("path", ""))
            query_string = scope["query_string"].decode("utf-8")

            if port == 443:
                port = None

            if scheme:
                url = f"{scheme}://"
            else:
                url = ""

            if port is not None:
                url += f"{host}:{port}{path}"
            else:
                url += f"{host}{path}"

            if query_string:
                url += "?" + query_string
            else:
                url += "/" if not url.endswith("/") else ""

        self._url = url

    def __str__(self):
        return self._url

    def __repr__(self):
        pattern = re.compile(r"(:)[^/]*?(@)")
        url = pattern.sub(r"\1********\2", self._url)
        return f"URL('{url}')"

    def __eq__(self, value):
        return value == self._url

    @property
    def components(self):
        if not hasattr(self, "_components"):
            components = urlparse(self._url)
            self._components = components
        return self._components

    @property
    def scheme(self):
        return self.components.scheme

    @property
    def hostname(self):
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

    @property
    def query(self):
        return self.components.query

    def replace(self, **kwargs):
        kwargs = {k: "" if v is None else v for k, v in kwargs.items()}

        if "hostname" in kwargs or "port" in kwargs:
            hostname = kwargs["hostname"] if "hostname" in kwargs else self.hostname
            port = kwargs["port"] if "port" in kwargs else self.port

            if port:
                netloc = f"{hostname}:{port}"
            else:
                netloc = f"{hostname}"

            kwargs.update(dict(netloc=netloc))

        kwargs.pop("hostname", None)
        kwargs.pop("port", None)

        components = self.components._replace(**kwargs)
        return URL(urlunparse(components))


class Headers(Mapping):
    def __init__(
        self, headers: dict[str, str] = None, raw: list[list[bytes, bytes]] = None
    ):
        self.headers = headers
        if headers is not None:
            self.raw = [
                (key.lower().encode("latin-1"), value.encode("latin-1"))
                for key, value in (headers or {}).items()
            ]

        else:
            self.raw = raw or []

    def __iter__(self):
        return iter([key.decode("latin-1").lower() for key, _ in self.raw])

    @property
    def scan(self):
        return [
            (key.decode("latin-1").lower(), value.decode("latin-1"))
            for key, value in self.raw
        ]

    def __contains__(self, name: str):
        for key, _ in self.scan:
            if key == name.lower():
                return True

        return False

    def __getitem__(self, name: str):
        for key, value in self.scan:
            if key == name.lower():
                return value

        raise KeyError(key)

    def __len__(self):
        return len(self.raw)

    def keys(self):
        return [key for key, _ in self.scan]

    def values(self):
        return [value for _, value in self.scan]

    def items(self):
        return [(key, value) for key, value in self.scan]

    def getlist(self, name: str):
        values = []
        for key, value in self.scan:
            if key == name.lower():
                values.append(value)

        return values

    def __repr__(self):
        if self.headers is not None:
            return f"Headers({self.headers})"

        return f"Headers(raw={self.raw})"

    def mutablecopy(self):
        return MutableHeaders(raw=self.raw)


class MutableHeaders(Headers):
    def __setitem__(self, name: str, value):
        setted = False
        for idx, (key, _) in enumerate(self.raw):
            if key.decode("latin-1") == name.lower():
                self.raw[idx] = (key, value.encode("latin-1"))
                setted = True

        if not setted:
            self.raw.append((name.lower().encode("latin-1"), value.encode("latin-1")))

    def __delitem__(self, name: str):
        for idx, (key, _) in enumerate(self.raw):
            if key.decode("latin-1") == name.lower():
                del self.raw[idx]

    def setdefault(self, name: str, value):
        for key, _ in self.raw:
            if key.decode("latin-1") == name.lower():
                break
        else:
            self.raw.append((name.lower().encode("latin-1"), value.encode("latin-1")))


class QueryParams(Mapping):
    def __init__(self, query_params: str | dict | list = ""):
        self.raw = defaultdict(list)

        if isinstance(query_params, bytes):
            query_params = query_params.decode()

        if isinstance(query_params, str):
            self.raw.update(parse_qs(query_params))

        elif isinstance(query_params, dict):
            for key, value in query_params.items():
                self.raw[key].append(value)

        elif isinstance(query_params, list):
            for key, value in query_params:
                self.raw[key].append(value)

        elif isinstance(query_params, QueryParams):
            self.raw = deepcopy(query_params.raw)

    def __contains__(self, key):
        return key in self.raw

    def __getitem__(self, key):
        if key not in self.raw:
            raise KeyError(key)

        return self.raw[key][-1]

    def __len__(self):
        return len(self.raw)

    def __iter__(self):
        return iter(self.raw.keys())

    def getlist(self, key):
        return self.raw[key]

    def __str__(self):
        pairs = []
        for key, values in self.raw.items():
            for value in values:
                pairs.append(f"{key}={value}")

        return "&".join(pairs)

    def __repr__(self):
        return f"QueryParams('{self}')"


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


class Secret:
    def __init__(self, secret):
        self._secret = secret

    def __repr__(self):
        return "Secret('**********')"

    def __str__(self):
        return self._secret
