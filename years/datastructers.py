from collections.abc import Mapping
from urllib.parse import parse_qsl


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
