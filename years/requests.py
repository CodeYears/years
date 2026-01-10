from collections.abc import Mapping
from years.datastructers import Hearders, QueryParams


class Request(Mapping):
    def __init__(self, scope, receive):
        self._scope = scope
        self._receive = receive

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
