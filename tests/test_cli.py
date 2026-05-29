from greet.cli import greeting


def test_greeting_basic():
    assert greeting("World") == "Hello, World!"


def test_greeting_shout():
    assert greeting("World", shout=True) == "HELLO, WORLD!"
