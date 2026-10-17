#!/usr/bin/env python
import subprocess
import sys
import time

from lib.java_backend import backend_dir, build_test_command
from lib.paths import BACKEND_TEST_LOG, REPO_ROOT, ensure_dir


def main() -> int:
    start = time.time()
    root = backend_dir(REPO_ROOT)
    backend_test_log = BACKEND_TEST_LOG
    ensure_dir(backend_test_log.parent)
    command = build_test_command(root)

    with open(backend_test_log, "w", encoding="utf-8") as log_file:
        test_result = subprocess.run(
            command,
            cwd=root,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

    if test_result.returncode != 0:
        print(f"Tests failed with exit code {test_result.returncode}")
        print(f"Full output saved to: {backend_test_log}")
        with open(backend_test_log, "r", encoding="utf-8", errors="ignore") as log_file:
            lines = log_file.readlines()
            print("\nLast 50 lines:")
            print("".join(lines[-50:]))
        return test_result.returncode

    elapsed = int(time.time() - start)
    print(f"Backend Acceptance: PASSED ({elapsed}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
