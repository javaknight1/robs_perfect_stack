#!/usr/bin/env python3
"""rob-stack CLI — new | check"""

import sys
from .generate import run_generate
from .check import run_check

HELP = """
╔══════════════════════════════════════╗
║      🚀  Rob's Stack CLI            ║
╚══════════════════════════════════════╝

Commands:
  rob-stack new              Create a new project from the canonical stack
  rob-stack check [path]     Check how closely a repo conforms to the stack
                             (defaults to current directory)

Options:
  -h, --help                 Show this help message
"""


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(HELP)
        return

    cmd = args[0]

    if cmd == "new":
        run_generate()
    elif cmd == "check":
        path = args[1] if len(args) > 1 else "."
        run_check(path)
    else:
        print(f"Unknown command: {cmd!r}")
        print(HELP)
        sys.exit(1)
