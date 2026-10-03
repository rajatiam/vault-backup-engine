import argparse, json
from .core import snapshot, verify, restore


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Content-addressed backup snapshots and verified restores"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("snapshot")
    create.add_argument("source")
    create.add_argument("vault")
    create.add_argument("--name", required=True)
    check = commands.add_parser("verify")
    check.add_argument("vault")
    check.add_argument("name")
    recover = commands.add_parser("restore")
    recover.add_argument("vault")
    recover.add_argument("name")
    recover.add_argument("target")
    args = parser.parse_args(argv)
    result = (
        snapshot(args.source, args.vault, args.name)
        if args.command == "snapshot"
        else (
            verify(args.vault, args.name)
            if args.command == "verify"
            else restore(args.vault, args.name, args.target)
        )
    )
    print(json.dumps(result, indent=2))
