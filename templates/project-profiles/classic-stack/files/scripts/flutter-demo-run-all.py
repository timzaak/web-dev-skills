#!/usr/bin/env python3
"""Discover and persist resumable batches of Android Patrol demo files."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from lib.paths import REPO_ROOT

QUALITY_DIR = REPO_ROOT / ".ai" / "quality"
PATROL_DIR = REPO_ROOT / "patrol_test"


def discover_test_files() -> list[Path]:
    if not PATROL_DIR.is_dir():
        return []
    return sorted(
        path for path in PATROL_DIR.rglob("*_test.dart")
        if "test-results" not in path.parts
    )


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def latest_running() -> Path | None:
    candidates = sorted(QUALITY_DIR.glob("flutter-demo-run-all-*.json"), reverse=True)
    for path in candidates:
        try:
            if json.loads(path.read_text(encoding="utf-8")).get("batch_status") == "running":
                return path
        except (OSError, json.JSONDecodeError):
            continue
    return None


def cmd_discover(args: argparse.Namespace) -> int:
    if args.continue_flag:
        report = latest_running()
        if not report:
            print(json.dumps({"error": "no running Flutter Demo batch"}))
            return 1
        payload = json.loads(report.read_text(encoding="utf-8"))
        entries = payload.get("entries", [])
        payload["resume_index"] = len(entries) if isinstance(entries, list) else 0
        payload["json_report"] = report.relative_to(REPO_ROOT).as_posix()
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        return 0

    files = [path.relative_to(REPO_ROOT).as_posix() for path in discover_test_files()]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report = QUALITY_DIR / f"flutter-demo-run-all-{stamp}.json"
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
    write_json(report, payload)
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0 if files else 1


def cmd_checkpoint(args: argparse.Namespace) -> int:
    path = args.json if args.json.is_absolute() else REPO_ROOT / args.json
    payload = json.loads(path.read_text(encoding="utf-8"))
    files = payload["discovered_files"]
    if args.index < 0 or args.index >= len(files):
        return 1
    payload["current_index"] = args.index
    payload["current_file"] = files[args.index]
    write_json(path, payload)
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    path = args.json if args.json.is_absolute() else REPO_ROOT / args.json
    payload = json.loads(path.read_text(encoding="utf-8"))
    current = str(payload.get("current_file", ""))
    if not current:
        return 1
    entries = payload.setdefault("entries", [])
    entries.append({
        "test_file": current,
        "status": args.status,
        "exit_code": args.exit_code,
        "duration": args.duration,
        "run_id": args.run_id,
        "logs": args.logs,
        "error": args.error if args.status == "failed" else "",
        "fixed": args.fixed,
    })
    payload["current_index"] = len(entries)
    payload["current_file"] = ""
    write_json(path, payload)
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    path = args.json if args.json.is_absolute() else REPO_ROOT / args.json
    payload = json.loads(path.read_text(encoding="utf-8"))
    files = payload.get("discovered_files", [])
    entries = payload.get("entries", [])
    if len(entries) != len(files):
        return 1
    payload["batch_status"] = "completed"
    payload["passed_files"] = sum(1 for entry in entries if entry.get("status") == "passed")
    payload["failed_files"] = len(entries) - int(payload["passed_files"])
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
    for entry in entries:
        lines.append(
            f"| {entry.get('test_file', '')} | {entry.get('status', '')} | "
            f"{entry.get('run_id', '')} | {entry.get('logs', '')} |"
        )
    markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        payload["markdown_report"] = markdown.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        payload["markdown_report"] = markdown.as_posix()
    write_json(path, payload)
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
