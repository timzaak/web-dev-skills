#!/usr/bin/env python
import sys

from lib.cli import require_executable, run_cmd
from lib.paths import REPO_ROOT


def main() -> int:
    cargo = require_executable("cargo")
    result = run_cmd([cargo, "fmt", "--", "--check"], cwd=REPO_ROOT / "backend")
    if result.returncode != 0:
        print("Code format check failed, run 'cargo fmt' to fix.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

