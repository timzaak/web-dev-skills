#!/usr/bin/env python
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from lib.cli import require_executable, run_cmd
from lib.paths import LOG_DIR, REPO_ROOT


def run_python_script(name: str) -> int:
    return subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / name)]).returncode


def health_check(url: str, retries: int = 3, delay: int = 2) -> bool:
    for i in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                if resp.status != 200:
                    continue
                payload = json.loads(resp.read().decode("utf-8"))
                if payload.get("status") == "healthy" and payload.get("database") is True and payload.get("redis") is True:
                    return True
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            pass
        if i < retries:
            time.sleep(delay)
    return False


def main() -> int:
    cargo = require_executable("cargo")
    start = time.time()
    backend_test_log = REPO_ROOT / "backend-test-output.log"
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

    if run_python_script("dev-start.py") != 0:
        print("Failed to start development environment")
        return 1

    time.sleep(10)

    backend_log = LOG_DIR / "backend.log"
    if not backend_log.exists():
        print(f"Backend log file not found: {backend_log}")
        run_python_script("dev-stop.py")
        return 1

    content = backend_log.read_text(encoding="utf-8", errors="ignore")
    if "Database migrations completed" not in content:
        if "duplicate key" in content and "_sqlx_migrations" in content:
            print("Migration conflict detected in backend log")
            run_python_script("dev-stop.py")
            return 1
        if "migration" in content.lower() and "error" in content.lower():
            print("Migration errors detected in backend log")
            run_python_script("dev-stop.py")
            return 1
    elapsed = int(time.time() - start)

    if not health_check("http://localhost:8080/health"):
        print("Health check failed after retries")
        run_python_script("dev-stop.py")
        return 1

    run_python_script("dev-stop.py")
    print(f"Backend Acceptance: PASSED ({elapsed}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

