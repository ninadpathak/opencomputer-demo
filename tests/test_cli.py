from greet.cli import greeting


def test_greeting_basic():
    assert greeting(["World"]) == "Hello, World!"


def test_greeting_shout():
    assert greeting(["World"], shout=True) == "HELLO, WORLD!"


def test_greeting_two_names():
    assert greeting(["Alice", "Bob"]) == "Hello, Alice and Bob!"


def test_greeting_multiple_names():
    assert greeting(["Alice", "Bob", "Carol"]) == "Hello, Alice, Bob and Carol!"


def test_greeting_multiple_names_shout():
    assert greeting(["Alice", "Bob"], shout=True) == "HELLO, ALICE AND BOB!"
