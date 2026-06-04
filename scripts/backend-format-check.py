#!/usr/bin/env python
import sys

from lib.cli import run_cmd
from lib.java_backend import backend_dir, build_format_check_command
from lib.paths import REPO_ROOT


def main() -> int:
    root = backend_dir(REPO_ROOT)
    if not root.is_dir():
        print("Backend directory not found; skipping backend format check.")
        return 0

    command = build_format_check_command(root)
    if command is None:
        print("No Java backend format/check task detected; skipping backend format check.")
        return 0

    result = run_cmd(command, cwd=root)
    if result.returncode != 0:
        print("Backend format/static check failed; run the project formatter/check task to fix it.")
        return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
