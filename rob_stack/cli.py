#!/usr/bin/env python3
"""rob-stack CLI — new | check | version"""

import sys
from .generate import run_generate
from .check import run_check

HELP = """
╔══════════════════════════════════════╗
║      🚀  Rob's Stack CLI            ║
╚══════════════════════════════════════╝

Commands:
  rob-stack new [--dry-run]    Create a new project from the canonical stack
  rob-stack check [path]       Check how closely a repo conforms to the stack
                               (defaults to current directory)
  rob-stack version            Print the installed version

Options:
  -h, --help                   Show this help message
  --version                    Print the installed version
  --dry-run                    (new) Preview files without writing
  --service <name>             (check) Check a single service only
  --json                       (check) Output results as JSON
"""


def _get_version() -> str:
    try:
        from importlib.metadata import version
        return version("rob-stack")
    except Exception:
        pass
    # Fallback: read from pyproject.toml
    try:
        from pathlib import Path
        toml = Path(__file__).resolve().parent.parent / "pyproject.toml"
        for line in toml.read_text().splitlines():
            if line.strip().startswith("version"):
                return line.split("=")[1].strip().strip('"')
    except Exception:
        pass
    return "unknown"


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(HELP)
        return

    cmd = args[0]

    if cmd in ("version", "--version"):
        print(f"rob-stack {_get_version()}")
        return

    if cmd == "new":
        dry_run = "--dry-run" in args
        run_generate(dry_run=dry_run)
    elif cmd == "check":
        # Parse check args: rob-stack check [path] [--service <name>] [--json]
        remaining = args[1:]
        json_output = "--json" in remaining
        remaining = [a for a in remaining if a != "--json"]
        path = "."
        service_filter = None
        i = 0
        while i < len(remaining):
            if remaining[i] == "--service" and i + 1 < len(remaining):
                service_filter = remaining[i + 1]
                i += 2
            elif not remaining[i].startswith("-"):
                path = remaining[i]
                i += 1
            else:
                i += 1
        run_check(path, service_filter=service_filter, json_output=json_output)
    else:
        print(f"Unknown command: {cmd!r}")
        print(HELP)
        sys.exit(1)
