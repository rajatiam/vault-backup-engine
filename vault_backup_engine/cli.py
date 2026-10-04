import argparse, json
from .core import snapshot, verify, restore, compare


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verified backups, restores and snapshot comparisons"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("snapshot")
    sub.add_argument("source")
    sub.add_argument("vault")
    sub.add_argument("--name", required=True)
    for name in ["verify", "restore"]:
        sub = commands.add_parser(name)
        sub.add_argument("vault")
        sub.add_argument("name")
        if name == "restore":
            sub.add_argument("target")
    sub = commands.add_parser("compare")
    sub.add_argument("vault")
    sub.add_argument("before")
    sub.add_argument("after")
    args = parser.parse_args(argv)
    if args.command == "snapshot":
        result = snapshot(args.source, args.vault, args.name)
    elif args.command == "verify":
        result = verify(args.vault, args.name)
    elif args.command == "restore":
        result = restore(args.vault, args.name, args.target)
    else:
        result = compare(args.vault, args.before, args.after)
    print(json.dumps(result, indent=2))
