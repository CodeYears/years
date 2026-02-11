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
