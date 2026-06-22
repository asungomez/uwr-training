"""Admin CLI dispatcher. Run via `make admin command='...'` or `python -m app.cli`.

Connects to the database in settings.database_url by default, or to --database-url
if given (use Render's external connection string to manage the deployed DB from
your laptop). One module per command lives alongside this file.
"""

import argparse

from app.cli import create_admin
from app.settings import settings

# Each command module exposes NAME, register(subparsers) and run(args).
COMMANDS = [create_admin]


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli", description="Admin CLI")
    parser.add_argument(
        "--database-url",
        default=settings.database_url,
        help="Override the target database (e.g. Render's external connection string).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    runners = {}
    for command in COMMANDS:
        command.register(subparsers)
        runners[command.NAME] = command.run

    args = parser.parse_args()
    runners[args.command](args)


if __name__ == "__main__":
    main()
