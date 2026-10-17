#!/usr/bin/env python
import os
import subprocess
import sys
from pathlib import Path

from lib.paths import REPO_ROOT, SCRIPTS_DIR


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: debug-test.py <test-file> [runner options]", file=sys.stderr)
        return 2
    test_file = sys.argv[1]
    args = [sys.executable, str(SCRIPTS_DIR / "web-demo-test-runner.py"), *sys.argv[1:]]
    args.extend(["--mode", "fast", "--log-level", "verbose"])

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
    result = subprocess.run(args, env=env, cwd=REPO_ROOT)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
