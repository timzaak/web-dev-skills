#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

from lib.paths import REPO_ROOT


def file_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if not path.exists():
        return 0
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup test logs for a run")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--test-name", required=True)
    parser.add_argument("--what-if", action="store_true", dest="what_if")
    args = parser.parse_args()

    deleted_count = 0
    recovered_space = 0
    print(f"Cleaning up logs for {args.test_name} (RunId: {args.run_id})")
    if args.what_if:
        print("WHATIF MODE: No files will be deleted")

    run_dir = REPO_ROOT / "demo" / "test-results" / "runs" / args.run_id
    if run_dir.exists():
        size = file_size(run_dir)
        if args.what_if:
            print(f"  Would delete: {run_dir} (~{round(size/1024,2)} KB)")
        else:
            for item in sorted(run_dir.rglob("*"), reverse=True):
                if item.is_file():
                    item.unlink(missing_ok=True)
                else:
                    item.rmdir()
            run_dir.rmdir()
            print(f"  Deleted: {run_dir} (~{round(size/1024,2)} KB)")
        deleted_count += 1
        recovered_space += size
    else:
        print(f"  Run directory not found: {run_dir}")

    unified = REPO_ROOT / "demo" / "test-results" / "unified-logs"
    for pattern in (f"{args.test_name}-*.log", f"{args.test_name}-*-network.json"):
        if not unified.exists():
            break
        for log in unified.glob(pattern):
            size = log.stat().st_size
            if args.what_if:
                print(f"  Would delete: {log} (~{round(size/1024,2)} KB)")
            else:
                log.unlink(missing_ok=True)
                print(f"  Deleted: {log.name} (~{round(size/1024,2)} KB)")
            deleted_count += 1
            recovered_space += size

    kb = round(recovered_space / 1024, 2)
    if args.what_if:
        print(f"WHATIF SUMMARY: Would delete {deleted_count} files (~{kb} KB)")
    else:
        print(f"Cleanup completed: {deleted_count} files, ~{kb} KB recovered")
    return 0


if __name__ == "__main__":
    sys.exit(main())

