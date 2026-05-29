import pytest

from greet import __version__
from greet.cli import build_parser, greeting


def test_greeting_basic():
    assert greeting("World") == "Hello, World!"


def test_greeting_shout():
    assert greeting("World", shout=True) == "HELLO, WORLD!"


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(["--version"])
    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"greet {__version__}"
