from collections.abc import MutableMapping


class Request(MutableMapping):
    def __init__(self, scope, receive):
        self._scope = scope
        self._receive = receive

    def __getitem__(self, key):
        return self._scope[key]

    def __setitem__(self, key, value):
        self._scope[key] = value

    def __delitem__(self, key):
        del self._scope[key]

    def __iter__(self):
        return iter(self._scope)

    def __len__(self):
        return len(self._scope)

    @property
    def method(self):
        return self["method"]
