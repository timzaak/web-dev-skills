#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

from lib.paths import REPO_ROOT


def clean_diagnostic_files(*, what_if: bool) -> tuple[int, int]:
    """Clean .ai/diagnose/*.md files."""
    dir_path = REPO_ROOT / ".ai" / "diagnose"
    if not dir_path.exists():
        return 0, 0

    count = 0
    recovered = 0
    for file in dir_path.glob("*.md"):
        size = file.stat().st_size
        if not what_if:
            file.unlink(missing_ok=True)
        count += 1
        recovered += size
    return count, recovered


def clean_evaluation_files(*, what_if: bool) -> tuple[int, int]:
    """Clean .ai/eval/*demo-eval.md files (except demo-eval-summary.md)."""
    dir_path = REPO_ROOT / ".ai" / "eval"
    if not dir_path.exists():
        return 0, 0

    count = 0
    recovered = 0
    for file in dir_path.glob("*demo-eval.md"):
        if file.name == "demo-eval-summary.md":
            continue
        size = file.stat().st_size
        if not what_if:
            file.unlink(missing_ok=True)
        count += 1
        recovered += size
    return count, recovered


def clean_unified_logs(*, what_if: bool) -> tuple[int, int]:
    """Clean demo/test-results/unified-logs/*.log and *-network.json files."""
    dir_path = REPO_ROOT / "demo" / "test-results" / "unified-logs"
    if not dir_path.exists():
        return 0, 0

    count = 0
    recovered = 0
    for pattern in ("*.log", "*-network.json"):
        for file in dir_path.glob(pattern):
            size = file.stat().st_size
            if not what_if:
                file.unlink(missing_ok=True)
            count += 1
            recovered += size
    return count, recovered


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup demo test artifacts")
    parser.add_argument("--what-if", action="store_true", dest="what_if",
                        help="Dry run: show what would be deleted without actually deleting")
    args = parser.parse_args()

    # Clean all file types
    clean_diagnostic_files(what_if=args.what_if)
    clean_evaluation_files(what_if=args.what_if)
    clean_unified_logs(what_if=args.what_if)

    # Print simple result
    print("clean all")

    return 0


if __name__ == "__main__":
    sys.exit(main())
