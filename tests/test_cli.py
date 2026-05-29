from greet.cli import greeting, main


def test_greeting_basic():
    assert greeting("World") == "Hello, World!"


def test_greeting_shout():
    assert greeting("World", shout=True) == "HELLO, WORLD!"


def test_repeat(capsys):
    main(["World", "--repeat", "3"])
    captured = capsys.readouterr()
    assert captured.out == "Hello, World!\nHello, World!\nHello, World!\n"
