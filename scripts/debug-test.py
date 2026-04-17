#!/usr/bin/env python
import os
import subprocess
import sys
from pathlib import Path

from lib.paths import REPO_ROOT


def main() -> int:
    test_file = sys.argv[1] if len(sys.argv) > 1 else ""
    args = [sys.executable, str(REPO_ROOT / "scripts" / "run-test-quiet.py")]
    if test_file:
        args.append(test_file)
    args.extend(["--log-level", "verbose"])

    env = dict(os.environ)
    env["DEBUG"] = "pw:api,pw:network"
    env["PLAYWRIGHT_TRACE"] = "on"

    print("=== Playwright Debug Mode ===")
    print(f"Test file: {test_file}")
    print("Mode: fast")
    print("DEBUG: pw:api,pw:network")
    print("TRACE: on")
    print("Log level: verbose")
    print("")
    print("Running test...")
    print("")
    result = subprocess.run(args, env=env)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

