import os
import pytest

from years.config import Config
from years.datastructures import URL


def test_config(tmpdir, monkeypatch):
    path = os.path.join(tmpdir, ".env")
    with open(path, "w") as file:
        file.write("# Do not commit to source control\n")
        file.write("DATABASE_URL=postgres://user:pass@localhost/dbname\n")
        file.write("REQUEST_HOSTNAME=example.com\n")
        file.write("SECRET_KEY=12345\n")
        file.write("BOOL_AS_INT=0\n")
        file.write("\n")
        file.write("\n")

    config = Config(path, environ={"DEBUG": "true"})

    DEBUG = config("DEBUG", cast=bool)
    DATABASE_URL = config("DATABASE_URL", cast=URL)
    REQUEST_TIMEOUT = config("REQUEST_TIMEOUT", cast=int, default=10)
    REQUEST_HOSTNAME = config("REQUEST_HOSTNAME")
    assert config("BOOL_AS_INT", cast=bool) is False

    assert DEBUG is True
    assert DATABASE_URL.path == "/dbname"
    assert DATABASE_URL.password == "pass"
    assert DATABASE_URL.username == "user"
    assert REQUEST_TIMEOUT == 10
    assert REQUEST_HOSTNAME == "example.com"

    with pytest.raises(KeyError):
        config.get("MISSING")

    with pytest.raises(ValueError):
        config.get("DEBUG", cast=int)

    with pytest.raises(ValueError):
        config.get("REQUEST_HOSTNAME", cast=bool)

    config = Config()
    monkeypatch.setenv("STARLETTE_EXAMPLE_TEST", "123")
    monkeypatch.setenv("BOOL_AS_INT", "1")
    assert config.get("STARLETTE_EXAMPLE_TEST", cast=int) == 123
    assert config.get("BOOL_AS_INT", cast=bool) is True

    monkeypatch.setenv("BOOL_AS_INT", "2")
    with pytest.raises(ValueError):
        config.get("BOOL_AS_INT", cast=bool)
