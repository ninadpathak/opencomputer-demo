import pytest

from greet import __version__
from greet.cli import greeting, build_parser


def test_greeting_basic():
    assert greeting("World") == "Hello, World!"


def test_greeting_shout():
    assert greeting("World", shout=True) == "HELLO, WORLD!"


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out
