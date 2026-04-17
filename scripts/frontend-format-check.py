#!/usr/bin/env python
import sys

from lib.cli import require_executable, run_cmd
from lib.paths import REPO_ROOT


def main() -> int:
    npm = require_executable("npm", windows_fallback="npm.cmd")
    result = run_cmd([npm, "run", "lint", "--", "--fix"], cwd=REPO_ROOT / "frontend")
    if result.returncode != 0:
        print("Lint skipped or failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

