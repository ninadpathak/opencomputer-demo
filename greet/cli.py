import argparse

from greet import __version__


def greeting(name: str, shout: bool = False) -> str:
    message = f"Hello, {name}!"
    return message.upper() if shout else message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="greet", description="A tiny greeting CLI.")
    parser.add_argument("name", help="who to greet")
    parser.add_argument("--shout", action="store_true", help="upper-case the greeting")
    parser.add_argument("--version", action="version", version=f"greet {__version__}")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    print(greeting(args.name, args.shout))


if __name__ == "__main__":
    main()
