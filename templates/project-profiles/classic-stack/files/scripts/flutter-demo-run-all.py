#!/usr/bin/env python3
"""Discover and persist resumable batches of Android Patrol demo files.

Batch state transitions and persistence are shared with
`web-demo-run-all.py` through `lib/batch_state.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from lib.batch_state import (
    QUALITY_DIR,
    BatchError,
    complete,
    ensure_quality_dir,
    latest_running_report,
    load_report,
    record_result,
    resolve_report_path,
    save_report,
    start_file,
)
from lib.paths import REPO_ROOT

REPORT_PREFIX = "flutter-demo-run-all"
PATROL_DIR = REPO_ROOT / "patrol_test"


def discover_test_files() -> list[Path]:
    if not PATROL_DIR.is_dir():
        return []
    return sorted(
        path for path in PATROL_DIR.rglob("*_test.dart")
        if "test-results" not in path.parts
    )


def print_json(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def cmd_discover(args: argparse.Namespace) -> int:
    if args.continue_flag:
        report = latest_running_report(REPORT_PREFIX)
        if not report:
            print(json.dumps({"error": "no running Flutter Demo batch"}))
            return 1
        payload = load_report(report)
        entries = payload.get("entries", [])
        payload["resume_index"] = len(entries) if isinstance(entries, list) else 0
        payload["json_report"] = report.relative_to(REPO_ROOT).as_posix()
        print_json(payload)
        return 0

    files = [path.relative_to(REPO_ROOT).as_posix() for path in discover_test_files()]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report = QUALITY_DIR / f"{REPORT_PREFIX}-{stamp}.json"
    payload: dict[str, object] = {
        "batch_status": "running",
        "batch_run_id": f"flutter-demo-all-{stamp}",
        "discovered_files": files,
        "entries": [],
        "current_index": 0,
        "current_file": "",
        "resume_index": 0,
        "json_report": report.relative_to(REPO_ROOT).as_posix(),
    }
    ensure_quality_dir()
    save_report(report, payload)
    print_json(payload)
    return 0 if files else 1


def cmd_checkpoint(args: argparse.Namespace) -> int:
    path = resolve_report_path(args.json)
    try:
        payload = load_report(path)
        start_file(payload, args.index)
        save_report(path, payload)
    except BatchError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    path = resolve_report_path(args.json)
    try:
        payload = load_report(path)
        record_result(
            payload,
            status=args.status,
            exit_code=args.exit_code,
            duration=args.duration,
            run_id=args.run_id,
            logs=args.logs,
            error=args.error,
            fixed=args.fixed,
        )
        save_report(path, payload)
    except BatchError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    path = resolve_report_path(args.json)
    try:
        payload = load_report(path)
        complete(payload)
    except BatchError as exc:
        print(f"ERROR: {exc}")
        return 1
    markdown = path.with_suffix(".md")
    lines = [
        "# Flutter Demo Run All Report",
        "",
        f"- Passed: {payload['passed_files']}",
        f"- Failed: {payload['failed_files']}",
        "",
        "| Test file | Status | Run ID | Logs |",
        "| --- | --- | --- | --- |",
    ]
    for entry in payload["entries"]:
        lines.append(
            f"| {entry.get('test_file', '')} | {entry.get('status', '')} | "
            f"{entry.get('run_id', '')} | {entry.get('logs', '')} |"
        )
    markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        payload["markdown_report"] = markdown.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        payload["markdown_report"] = markdown.as_posix()
    save_report(path, payload)
    return 0 if payload["failed_files"] == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Flutter Demo batch state helper")
    sub = parser.add_subparsers(dest="command", required=True)
    discover = sub.add_parser("discover")
    discover.add_argument("continue_flag", nargs="?", choices=["continue"])
    discover.set_defaults(func=cmd_discover)
    checkpoint = sub.add_parser("checkpoint")
    checkpoint.add_argument("--json", type=Path, required=True)
    checkpoint.add_argument("--index", type=int, required=True)
    checkpoint.set_defaults(func=cmd_checkpoint)
    record = sub.add_parser("record")
    record.add_argument("--json", type=Path, required=True)
    record.add_argument("--status", choices=["passed", "failed"], required=True)
    record.add_argument("--exit-code", type=int, default=0)
    record.add_argument("--duration", type=float, default=0.0)
    record.add_argument("--run-id", default="")
    record.add_argument("--logs", default="")
    record.add_argument("--error", default="")
    record.add_argument("--fixed", action="store_true")
    record.set_defaults(func=cmd_record)
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--json", type=Path, required=True)
    finalize.set_defaults(func=cmd_finalize)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
