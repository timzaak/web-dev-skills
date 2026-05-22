#!/usr/bin/env python
import subprocess
import sys
import time

from lib.cli import require_executable
from lib.paths import BACKEND_TEST_LOG, REPO_ROOT, ensure_dir


def main() -> int:
    cargo = require_executable("cargo")
    start = time.time()
    backend_test_log = BACKEND_TEST_LOG
    ensure_dir(backend_test_log.parent)
    with open(backend_test_log, "w", encoding="utf-8") as log_file:
        test_result = subprocess.run(
            [cargo, "nextest", "run", "--workspace"],
            cwd=REPO_ROOT / "backend",
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True
        )
    if test_result.returncode != 0:
        print(f"Tests failed with exit code {test_result.returncode}")
        print(f"Full output saved to: {backend_test_log}")
        # Show last 50 lines for quick error diagnosis
        with open(backend_test_log, "r", encoding="utf-8", errors="ignore") as log_file:
            lines = log_file.readlines()
            print("\nLast 50 lines:")
            print("".join(lines[-50:]))
        return 1

    elapsed = int(time.time() - start)
    print(f"Backend Acceptance: PASSED ({elapsed}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
