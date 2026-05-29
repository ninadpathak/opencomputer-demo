import argparse


def greeting(names: list[str], shout: bool = False) -> str:
    if len(names) == 1:
        joined = names[0]
    else:
        joined = ", ".join(names[:-1]) + " and " + names[-1]
    message = f"Hello, {joined}!"
    return message.upper() if shout else message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="greet", description="A tiny greeting CLI.")
    parser.add_argument("names", nargs="+", help="who to greet")
    parser.add_argument("--shout", action="store_true", help="upper-case the greeting")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    print(greeting(args.names, args.shout))


if __name__ == "__main__":
    main()
