import os
import pathlib


def judge_bool(value: str):
    if value in ["0", "1"]:
        return bool(int(value))

    if value.lower() in ["true", "false"]:
        return True if value.lower() == "true" else False

    raise ValueError(value)


class Config:
    def __init__(self, path: str = None, environ: dict = None):
        self._config = {}

        if environ is not None:
            self._config.update(environ)

        if path is not None:
            self.load(path)

    def load(self, path: pathlib.Path | str):

        if isinstance(path, str):
            path = pathlib.Path(path)

        lines = path.read_text().strip().split("\n")
        for line in lines:
            if line.startswith("#"):
                continue

            key, value = line.split("=")
            self._config[key] = value

    def __call__(self, name: str, cast=None, default=None):

        environ = False
        if os.environ.get(name, default):
            value = os.environ.get(name, default)
            environ = True

        if not environ:
            if default is not None:
                value = self._config.get(name, default)

            else:
                value = self._config[name]

        if cast is not None:
            if cast is bool:
                value = judge_bool(value)
            else:
                value = cast(value)

        return value

    def get(self, name: str, cast=None, default=None):
        return self(name, cast, default)


class EnvironError(Exception):
    """环境变量键异常"""


class Environ:
    def __init__(self):
        self.freeze = set()

    def __len__(self):
        return len(os.environ)

    def __setitem__(self, name: str, value):
        if name in self.freeze:
            raise EnvironError(name)

        os.environ[name] = value

    def __getitem__(self, name: str):
        try:
            value = os.environ[name]
            self.freeze.add(name)
            return value
        except KeyError:
            raise EnvironError(name)

    def __iter__(self):
        return iter(os.environ.keys())

    def __delitem__(self, name: str):
        try:
            del os.environ[name]
        except KeyError:
            raise EnvironError(name)
