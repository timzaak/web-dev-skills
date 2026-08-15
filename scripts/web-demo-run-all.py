#!/usr/bin/env python3
"""
Discovery + reporting helper for batch Demo E2E runs.

This script is intentionally side-effect-free at execution time: it does NOT
run tests or spawn nested `claude` processes. The actual per-file loop, the
diagnose -> fix -> rerun repair cycle, and the demo-environment restart are
driven by the `/t-tools:t-web-demo-run-all` skill in the main session. Driving the batch
from the main session (short, observable Bash/Agent calls with file-backed
checkpoints) replaces the old blocking nested-CLI workflow
subprocess loop, which froze the parent session for up to hours.

Subcommands:
  discover [continue] [--filter-file F] [--report-prefix P]
      Enumerate non-live demo test files. In fresh mode, write the initial
      batch JSON payload. In continue mode, read the latest batch JSON and
      compute the resume index. Prints a single JSON line on stdout that the
      skill consumes (discovered_files, batch_run_id, json_report, md_report,
      resume_index, resumed_from).

  finalize --json <path>
      Read the batch JSON written/updated by the skill, render the Markdown
      report from its entries, set batch_status=completed, and write both
      files back.

  checkpoint --json <path> --index N
      Mark one discovered file as current without rewriting JSON in the main
      session.

  record --json <path> --status passed|failed [...]
      Append the current file's compact result and advance the checkpoint.

  block --json <path> --error <message>
      Preserve the current checkpoint and record a blocking environment error.

  (no subcommand)
      Print guidance. Direct batch execution must go through /t-tools:t-web-demo-run-all.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from lib.paths import REPO_ROOT

# Configure UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

QUALITY_DIR = REPO_ROOT / ".ai" / "quality"
E2E_DIR = REPO_ROOT / "demo" / "e2e"
EXCLUDED_DIR_NAMES = {"fixtures", "templates", "verification", "live"}


@dataclass
class RunEntry:
    test_file: str
    status: str
    exit_code: int
    duration: float
    run_id: str
    logs: str
    summary: dict[str, object]
    error: str = ""
    fixed: bool = False


def now_display() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def discover_test_files(*, filter_file: Path | None = None) -> list[Path]:
    all_files: list[Path] = []
    for path in sorted(E2E_DIR.rglob("*.e2e.ts")):
        rel = path.relative_to(E2E_DIR)
        if any(part in EXCLUDED_DIR_NAMES for part in rel.parts):
            continue
        if "test-" in path.name:
            continue
        all_files.append(path)

    if filter_file is None:
        return all_files

    filter_path = filter_file if filter_file.is_absolute() else REPO_ROOT / filter_file
    if not filter_path.exists():
        raise FileNotFoundError(f"Filter file not found: {filter_path}")

    wanted: set[str] = set()
    for line in filter_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        wanted.add(stripped)

    return [
        path
        for path in all_files
        if path.relative_to(E2E_DIR).as_posix() in wanted
    ]


def load_json_report(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_report(path: Path, payload: dict[str, object]) -> None:
    payload["updated_at"] = now_display()
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def resolve_report_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def find_latest_json_report(report_prefix: str) -> Path | None:
    candidates = sorted(
        QUALITY_DIR.glob(f"{report_prefix}-*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def payload_entry_paths(payload: dict[str, object]) -> list[str]:
    files = payload.get("discovered_files")
    if not isinstance(files, list) or not files:
        raise ValueError("Latest batch report does not contain discovered_files")
    normalized = [str(item) for item in files]
    if any(not item for item in normalized):
        raise ValueError("Latest batch report contains an invalid discovered_files entry")
    return normalized


def determine_resume_index(payload: dict[str, object]) -> int:
    discovered_files = payload_entry_paths(payload)
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Latest batch report does not contain entries")

    if payload.get("batch_status") != "running":
        raise ValueError("Latest batch is not running and cannot be continued")

    completed_files: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Latest batch report contains a non-object entry")
        test_file = str(entry.get("test_file", ""))
        if not test_file:
            raise ValueError("Latest batch report contains an entry without test_file")
        completed_files.append(test_file)

    expected_prefix = discovered_files[:len(completed_files)]
    if completed_files != expected_prefix:
        raise ValueError("Latest batch entries are not a completed prefix of discovered_files")

    current_file = payload.get("current_file")
    if isinstance(current_file, str) and current_file:
        try:
            resume_index = discovered_files.index(current_file)
        except ValueError as exc:
            raise ValueError(f"current_file not found in discovered_files: {current_file}") from exc
        if resume_index != len(entries):
            raise ValueError("current_file does not immediately follow the completed entries")
        return resume_index

    current_index = payload.get("current_index", len(entries))
    if not isinstance(current_index, int) or isinstance(current_index, bool):
        raise ValueError("Latest batch report contains an invalid current_index")
    if current_index != len(entries):
        raise ValueError("current_index does not match the completed entry count")
    return current_index


def build_fresh_payload(
    *,
    report_prefix: str,
    test_files: list[Path],
    json_report_path: Path,
    md_report_path: Path,
) -> dict[str, object]:
    return {
        "generated_at": now_display(),
        "updated_at": now_display(),
        "report_prefix": report_prefix,
        "batch_status": "running",
        "invocation": "fresh",
        "total_duration": 0.0,
        "total_files": len(test_files),
        "passed_files": 0,
        "failed_files": 0,
        "current_index": 0,
        "current_file": "",
        "discovered_files": [path.relative_to(REPO_ROOT).as_posix() for path in test_files],
        "entries": [],
        "json_report": json_report_path.relative_to(REPO_ROOT).as_posix(),
        "markdown_report": md_report_path.relative_to(REPO_ROOT).as_posix(),
        "started_at": now_display(),
    }


def restore_payload_for_continue(
    *,
    report_prefix: str,
) -> tuple[dict[str, object], Path, Path, list[Path], int]:
    json_report_path = find_latest_json_report(report_prefix)
    if json_report_path is None:
        raise ValueError(f"No previous {report_prefix} JSON report found")

    payload = load_json_report(json_report_path)
    discovered_files = payload_entry_paths(payload)
    resume_index = determine_resume_index(payload)

    if resume_index >= len(discovered_files):
        raise ValueError("Latest batch has nothing left to continue")

    md_value = payload.get("markdown_report")
    if not isinstance(md_value, str) or not md_value:
        md_report_path = json_report_path.with_suffix(".md")
    else:
        md_report_path = REPO_ROOT / md_value.replace("/", "\\")

    test_files = [REPO_ROOT / rel_path.replace("/", "\\") for rel_path in discovered_files]
    missing = [path.relative_to(REPO_ROOT).as_posix() for path in test_files if not path.exists()]
    if missing:
        raise ValueError(f"Cannot continue because test files no longer exist: {', '.join(missing)}")

    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Latest batch report does not contain entries")

    payload["entries"] = entries
    payload["batch_status"] = "running"
    payload["invocation"] = "continue"
    payload["current_index"] = resume_index
    payload["current_file"] = discovered_files[resume_index]
    payload["total_files"] = len(discovered_files)
    payload["passed_files"] = sum(
        1 for entry in payload["entries"] if isinstance(entry, dict) and str(entry.get("status", "")) == "passed"
    )
    payload["failed_files"] = sum(
        1 for entry in payload["entries"] if isinstance(entry, dict) and str(entry.get("status", "")) == "failed"
    )
    return payload, json_report_path, md_report_path, test_files, resume_index


def build_markdown_report(
    *,
    generated_at: str,
    total_duration: float,
    entries: list[RunEntry],
    json_report_path: Path,
) -> str:
    total = len(entries)
    passed = sum(1 for entry in entries if entry.status == "passed" and not entry.fixed)
    fixed = sum(1 for entry in entries if entry.fixed)
    failed = sum(1 for entry in entries if entry.status == "failed" and not entry.fixed)
    pass_rate = 0.0 if total == 0 else round(((passed + fixed) / total) * 100, 1)

    lines = [
        "# Web Demo Run All Report",
        "",
        f"- Generated at: {generated_at}",
        f"- Total files: {total}",
        f"- Passed: {passed}",
        f"- Fixed: {fixed}",
        f"- Failed: {failed}",
        f"- Pass rate: {pass_rate}%",
        f"- Total duration: {round(total_duration, 1)}s",
        f"- JSON summary: `{json_report_path.relative_to(REPO_ROOT).as_posix()}`",
        "",
        "## File Results",
        "",
        "| File | Status | Duration | Exit Code | Logs |",
        "| --- | --- | ---: | ---: | --- |",
    ]

    for entry in entries:
        if entry.status == "passed" and not entry.fixed:
            status_icon = "PASS"
        elif entry.fixed:
            status_icon = "FIXED"
        else:
            status_icon = "FAIL"
        logs = f"`{entry.logs}`" if entry.logs else "-"
        lines.append(
            f"| `{entry.test_file}` | {status_icon} | {entry.duration}s | {entry.exit_code} | {logs} |"
        )

    fixed_entries = [entry for entry in entries if entry.fixed]
    if fixed_entries:
        lines.extend(["", "## Fixed Files", ""])
        lines.append("The following files initially failed but were successfully fixed:")
        lines.append("")
        for entry in fixed_entries:
            lines.append(f"- `{entry.test_file}`")
            if entry.logs:
                lines.append(f"  - logs: `{entry.logs}`")

    failed_entries = [entry for entry in entries if entry.status == "failed" and not entry.fixed]
    lines.extend(["", "## Unfixed Files", ""])
    if not failed_entries:
        lines.append("None. All tests passed or were successfully fixed.")
    else:
        for entry in failed_entries:
            lines.append(f"- `{entry.test_file}`")
            if entry.error:
                lines.append(f"  - error: {entry.error}")
            if entry.logs:
                lines.append(f"  - logs: `{entry.logs}`")

    lines.extend([
        "",
        "## Suggested Next Step",
        "",
    ])

    if failed_entries:
        lines.extend([
            "For unfixed files, review the error details above. Consider:",
            "1. Running individual tests with verbose logging: `/t-tools:t-web-demo-run [file]`",
            "2. Checking the logs for specific failure patterns",
            "3. Manual investigation or targeted fixes based on error messages",
        ])
    else:
        lines.append("All tests passed or were automatically fixed. No manual intervention needed.")

    return "\n".join(lines) + "\n"


def ensure_quality_dir() -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)


def print_json_stdout(payload: dict[str, object]) -> None:
    """Print a single JSON line on stdout for the skill to parse."""
    print(json.dumps(payload, ensure_ascii=False))


# --------------------------------------------------------------------------- #
# Subcommand: discover
# --------------------------------------------------------------------------- #

def cmd_discover(args: argparse.Namespace) -> int:
    try:
        test_files = discover_test_files(filter_file=args.filter_file)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1
    if not test_files:
        print("ERROR: No demo test files found")
        return 1

    ensure_quality_dir()
    is_continue = args.continue_flag

    if is_continue:
        try:
            payload, json_report_path, md_report_path, test_files, resume_index = restore_payload_for_continue(
                report_prefix=args.report_prefix,
            )
        except ValueError as exc:
            print(f"ERROR: {exc}")
            return 1
        write_json_report(json_report_path, payload)
        batch_run_id = Path(str(json_report_path.stem)).name
        resumed_from = test_files[resume_index].relative_to(REPO_ROOT).as_posix()
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        json_report_path = QUALITY_DIR / f"{args.report_prefix}-{timestamp}.json"
        md_report_path = QUALITY_DIR / f"{args.report_prefix}-{timestamp}.md"
        payload = build_fresh_payload(
            report_prefix=args.report_prefix,
            test_files=test_files,
            json_report_path=json_report_path,
            md_report_path=md_report_path,
        )
        write_json_report(json_report_path, payload)
        batch_run_id = f"run-all-{timestamp}"
        resume_index = 0
        resumed_from = ""

    discovered_rel = [path.relative_to(REPO_ROOT).as_posix() for path in test_files]
    print_json_stdout({
        "discovered_files": discovered_rel,
        "batch_run_id": batch_run_id,
        "json_report": json_report_path.relative_to(REPO_ROOT).as_posix(),
        "md_report": md_report_path.relative_to(REPO_ROOT).as_posix(),
        "resume_index": resume_index,
        "resumed_from": resumed_from,
        "invocation": "continue" if is_continue else "fresh",
        "total_files": len(discovered_rel),
    })
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    report_path = resolve_report_path(args.json)
    try:
        payload = load_json_report(report_path)
        discovered_files = payload_entry_paths(payload)
        entries = payload.get("entries")
        if payload.get("batch_status") != "running":
            raise ValueError("Batch is not running")
        if not isinstance(entries, list):
            raise ValueError("Batch report does not contain entries")
        if args.index != len(entries):
            raise ValueError("Checkpoint index must equal the completed entry count")
        if args.index < 0 or args.index >= len(discovered_files):
            raise ValueError("Checkpoint index is out of range")
        payload["current_index"] = args.index
        payload["current_file"] = discovered_files[args.index]
        payload.pop("last_error", None)
        write_json_report(report_path, payload)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    report_path = resolve_report_path(args.json)
    try:
        payload = load_json_report(report_path)
        discovered_files = payload_entry_paths(payload)
        entries = payload.get("entries")
        if payload.get("batch_status") != "running":
            raise ValueError("Batch is not running")
        if not isinstance(entries, list):
            raise ValueError("Batch report does not contain entries")
        index = len(entries)
        if index >= len(discovered_files):
            raise ValueError("Batch already contains all file results")
        expected_file = discovered_files[index]
        if payload.get("current_file") != expected_file:
            raise ValueError("Current file does not match the next unfinished file")
        if args.fixed and args.status != "passed":
            raise ValueError("Only a passed result can be marked fixed")

        entries.append({
            "test_file": expected_file,
            "status": args.status,
            "exit_code": args.exit_code,
            "duration": args.duration,
            "run_id": args.run_id,
            "logs": args.logs,
            "error": args.error if args.status == "failed" else "",
            "fixed": args.fixed,
        })
        payload["current_index"] = index + 1
        payload["current_file"] = ""
        payload["passed_files"] = sum(
            1 for entry in entries if isinstance(entry, dict) and entry.get("status") == "passed"
        )
        payload["failed_files"] = len(entries) - int(payload["passed_files"])
        payload["total_duration"] = round(sum(
            float(entry.get("duration", 0.0) or 0.0)
            for entry in entries
            if isinstance(entry, dict)
        ), 3)
        payload.pop("last_error", None)
        write_json_report(report_path, payload)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


def cmd_block(args: argparse.Namespace) -> int:
    report_path = resolve_report_path(args.json)
    try:
        payload = load_json_report(report_path)
        if payload.get("batch_status") != "running" or not payload.get("current_file"):
            raise ValueError("Batch has no active file checkpoint")
        payload["last_error"] = args.error
        write_json_report(report_path, payload)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


# --------------------------------------------------------------------------- #
# Subcommand: scan / scan-record / cluster (shared-root-cause optimization)
#
# Like discover/checkpoint/record, these stay side-effect-free re: test
# execution: the script never runs tests or spawns Claude. The skill
# `/t-tools:t-web-demo-run-all scan` drives `web-demo-test-runner.py` via Bash and calls
# `scan` to initialize `scan_results[]`, `scan --file ...` to record each
# file's outcome, then `cluster` to read the failing runs' Playwright logs
# and group them by normalized error fingerprint.
# --------------------------------------------------------------------------- #

def build_scan_entry(test_file: str) -> dict[str, object]:
    return {
        "test_file": test_file,
        "status": "pending",
        "exit_code": None,
        "duration": 0.0,
        "run_id": "",
        "logs": "",
    }


def _has_scan_results(payload: dict[str, object]) -> bool:
    results = payload.get("scan_results")
    return isinstance(results, list) and len(results) > 0


def cmd_scan(args: argparse.Namespace) -> int:
    report_path = resolve_report_path(args.json)
    try:
        payload = load_json_report(report_path)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    # Record mode: a specific file was supplied.
    if args.file:
        try:
            discovered_files = payload_entry_paths(payload)
            results = payload.get("scan_results")
            if not isinstance(results, list) or not results:
                raise ValueError("scan_results is empty; run `scan` without --file first")
            target = next(
                (entry for entry in results
                 if isinstance(entry, dict) and str(entry.get("test_file", "")) == args.file),
                None,
            )
            if target is None:
                raise ValueError(f"{args.file} not found in scan_results")
            if args.status not in {"passed", "failed"}:
                raise ValueError("status must be passed or failed")
            target["status"] = args.status
            target["exit_code"] = args.exit_code
            target["duration"] = args.duration
            target["run_id"] = args.run_id
            target["logs"] = args.logs
            write_json_report(report_path, payload)
        except ValueError as exc:
            print(f"ERROR: {exc}")
            return 1
        print_json_stdout({
            "recorded": args.file,
            "status": args.status,
            "pending": sum(
                1 for entry in payload.get("scan_results", [])
                if isinstance(entry, dict) and entry.get("status") == "pending"
            ),
        })
        return 0

    # Init mode: (re)build scan_results[] for every discovered file.
    try:
        discovered_files = payload_entry_paths(payload)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    if _has_scan_results(payload) and not args.force:
        results = payload.get("scan_results")
        pending = sum(
            1 for entry in results
            if isinstance(entry, dict) and entry.get("status") == "pending"
        )
        print_json_stdout({
            "scan_run_id": payload.get("scan_run_id", ""),
            "already_initialized": True,
            "total": len(results) if isinstance(results, list) else 0,
            "pending": pending,
        })
        return 0

    scan_run_id = args.scan_run_id or f"run-all-scan-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    payload["scan_run_id"] = scan_run_id
    payload["scan_results"] = [build_scan_entry(file_path) for file_path in discovered_files]
    write_json_report(report_path, payload)
    print_json_stdout({
        "scan_run_id": scan_run_id,
        "already_initialized": False,
        "total": len(discovered_files),
        "pending": len(discovered_files),
        "files": discovered_files,
    })
    return 0


# Failure extraction + clustering for the `cluster` subcommand. Kept tolerant:
# Playwright output formats vary across versions; when in doubt a failure
# becomes its own single-member cluster rather than silently merging.

_FAILURE_TITLE = re.compile(r"\s*[✗×✘]\s*\d+.*?›\s*(.+?)\s*(?:\([\d.]+s\))?\s*$")
_ERROR_LINE = re.compile(
    r"^\s*(Error:|TimeoutError|expect\(|AssertionError|locator\.|page\.|"
    r"\b[45]\d{2}\b|ECONNREFUSED|net::ERR)"
)
_SELECTOR = re.compile(r"(\[data-testid=[^\]]+\]|getByRole\([^)]+\)|page\.\w+\([^)]+\)|/api/[^\s\"']+)")
_STATUS_CODE = re.compile(r"\b([45]\d{2})\b")


def _read_log_safely(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _normalize_fingerprint(error_line: str, selector: str) -> str:
    family = "unknown"
    lower = error_line.lower()
    if "timeout" in lower:
        family = "timeout"
    elif "expect(" in lower or "assertionerror" in lower:
        family = "assertion"
    elif "selector" in lower or "locator" in lower or "not found" in lower:
        family = "selector"
    elif "/api/" in lower:
        family = "api"
    elif "econnrefused" in lower or "net::err" in lower:
        family = "network"
    else:
        match = _STATUS_CODE.search(error_line)
        if match:
            family = f"http-{match.group(1)}"

    token = selector.strip().replace("\n", " ")
    token = re.sub(r"\s+", " ", token)
    if not token:
        return family
    return f"{family}|{token}"


def parse_playwright_failures(log_text: str) -> list[dict[str, str]]:
    """Extract failure cases from a Playwright output log.

    Returns a list of dicts with keys: case_title, error_line, selector.
    Robust to missing sections: an empty log yields an empty list.
    """
    failures: list[dict[str, str]] = []
    current_title: str | None = None
    first_error: str = ""
    first_selector: str = ""

    for raw_line in log_text.splitlines():
        title_match = _FAILURE_TITLE.match(raw_line)
        if title_match:
            if current_title is not None:
                failures.append({
                    "case_title": current_title,
                    "error_line": first_error,
                    "selector": first_selector,
                })
            current_title = title_match.group(1).strip()
            first_error = ""
            first_selector = ""
            continue

        if current_title is not None:
            if not first_error and _ERROR_LINE.match(raw_line):
                first_error = raw_line.strip()
            if not first_selector:
                selector_match = _SELECTOR.search(raw_line)
                if selector_match:
                    first_selector = selector_match.group(1)

    if current_title is not None:
        failures.append({
            "case_title": current_title,
            "error_line": first_error,
            "selector": first_selector,
        })

    return failures


def build_clusters(
    failed_results: list[dict[str, object]],
    log_root: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Group failed scan results by normalized error fingerprint.

    Returns (clusters, unclusterable). Each cluster dict has: fingerprint,
    representative_error, affected_files[], affected_cases[]. Unclusterable
    entries (no run_id, unreadable log, or no parseable failures) are returned
    separately so the caller can surface them rather than drop them silently.
    """
    buckets: dict[str, dict[str, object]] = {}
    unclusterable: list[dict[str, object]] = []

    for result in failed_results:
        test_file = str(result.get("test_file", ""))
        run_id = str(result.get("run_id", "") or "")
        if not run_id:
            unclusterable.append({"test_file": test_file, "reason": "missing run_id"})
            continue

        log_path = log_root / run_id / "playwright-output.log"
        if not log_path.exists():
            unclusterable.append({
                "test_file": test_file,
                "run_id": run_id,
                "reason": "log not found",
            })
            continue

        failures = parse_playwright_failures(_read_log_safely(log_path))
        if not failures:
            unclusterable.append({
                "test_file": test_file,
                "run_id": run_id,
                "reason": "no parseable failures",
            })
            continue

        for failure in failures:
            fingerprint = _normalize_fingerprint(failure["error_line"], failure["selector"])
            bucket = buckets.setdefault(fingerprint, {
                "fingerprint": fingerprint,
                "representative_error": failure["error_line"] or failure["case_title"],
                "affected_files": [],
                "affected_cases": [],
            })
            if test_file not in bucket["affected_files"]:
                bucket["affected_files"].append(test_file)
            bucket["affected_cases"].append({
                "test_file": test_file,
                "case_title": failure["case_title"],
            })

    clusters = sorted(buckets.values(), key=lambda bucket: len(bucket["affected_files"]), reverse=True)
    return clusters, unclusterable


def cmd_cluster(args: argparse.Namespace) -> int:
    report_path = resolve_report_path(args.json)
    try:
        payload = load_json_report(report_path)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    results = payload.get("scan_results")
    source = "scan_results"
    if not isinstance(results, list) or not results:
        results = payload.get("entries")
        source = "entries"
        if not isinstance(results, list) or not results:
            print("ERROR: batch JSON has no scan_results or entries to cluster")
            return 1

    failed_results = [
        entry for entry in results
        if isinstance(entry, dict) and str(entry.get("status", "")) == "failed"
    ]
    passed_count = sum(
        1 for entry in results
        if isinstance(entry, dict) and str(entry.get("status", "")) == "passed"
    )

    log_root = REPO_ROOT / "demo" / "test-results" / "runs"
    clusters, unclusterable = build_clusters(failed_results, log_root)

    print_json_stdout({
        "source": source,
        "total_files": len(results),
        "passed": passed_count,
        "failed": len(failed_results),
        "unique_clusters": len(clusters),
        "clusters": clusters,
        "unclusterable": unclusterable,
    })
    return 0
    return 0


# --------------------------------------------------------------------------- #
# Subcommand: finalize
# --------------------------------------------------------------------------- #

def cmd_finalize(args: argparse.Namespace) -> int:
    json_report_path = resolve_report_path(args.json)
    if not json_report_path.exists():
        print(f"ERROR: batch JSON not found: {json_report_path}")
        return 1

    payload = load_json_report(json_report_path)
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        print("ERROR: batch JSON does not contain entries")
        return 1

    try:
        discovered_files = payload_entry_paths(payload)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    if len(raw_entries) != len(discovered_files):
        print(
            "ERROR: batch is incomplete: "
            f"expected {len(discovered_files)} entries, found {len(raw_entries)}"
        )
        return 1

    entries: list[RunEntry] = []
    for index, entry in enumerate(raw_entries):
        if not isinstance(entry, dict):
            print(f"ERROR: entry {index} is not an object")
            return 1
        expected_file = discovered_files[index]
        actual_file = str(entry.get("test_file", ""))
        if actual_file != expected_file:
            print(
                f"ERROR: entry {index} test_file mismatch: "
                f"expected {expected_file}, found {actual_file or '<empty>'}"
            )
            return 1
        status = str(entry.get("status", ""))
        if status not in {"passed", "failed"}:
            print(f"ERROR: entry {index} has invalid status: {status or '<empty>'}")
            return 1
        fixed = parse_boolish(entry.get("fixed", False))
        if fixed and status != "passed":
            print(f"ERROR: entry {index} cannot be fixed unless status is passed")
            return 1
        entries.append(
            RunEntry(
                test_file=actual_file,
                status=status,
                exit_code=int(entry.get("exit_code", 0) or 0),
                duration=float(entry.get("duration", 0.0) or 0.0),
                run_id=str(entry.get("run_id", "")),
                logs=str(entry.get("logs", "")),
                summary=entry.get("summary", {}) if isinstance(entry.get("summary", {}), dict) else {},
                error=str(entry.get("error", "")),
                fixed=fixed,
            )
        )

    total_duration = float(payload.get("total_duration", 0.0) or 0.0)
    passed_count = sum(1 for entry in entries if entry.status == "passed")
    failed_count = len(entries) - passed_count

    md_value = payload.get("markdown_report")
    if isinstance(md_value, str) and md_value:
        md_report_path = REPO_ROOT / md_value.replace("/", "\\")
    else:
        md_report_path = json_report_path.with_suffix(".md")

    generated_at = now_display()
    json_payload = {
        **payload,
        "generated_at": payload.get("generated_at", generated_at),
        "batch_status": "completed",
        "total_duration": total_duration,
        "total_files": len(discovered_files),
        "passed_files": passed_count,
        "failed_files": failed_count,
        "current_index": len(entries),
        "current_file": "",
        "entries": [asdict(entry) for entry in entries],
    }
    write_json_report(json_report_path, json_payload)
    md_report_path.write_text(
        build_markdown_report(
            generated_at=generated_at,
            total_duration=total_duration,
            entries=entries,
            json_report_path=json_report_path,
        ),
        encoding="utf-8",
    )

    print(f"Markdown: {md_report_path.relative_to(REPO_ROOT).as_posix()}")
    print(f"JSON: {json_report_path.relative_to(REPO_ROOT).as_posix()}")
    print(f"Passed: {passed_count}  Failed: {failed_count}")
    return 0 if failed_count == 0 else 1


# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Discovery + reporting helper for batch Demo E2E runs. "
            "Test execution is driven by /t-tools:t-web-demo-run-all in the main session."
        )
    )
    sub = parser.add_subparsers(dest="command")

    p_discover = sub.add_parser(
        "discover",
        help="Enumerate non-live demo files; write/resume batch JSON; print plan JSON.",
    )
    p_discover.add_argument(
        "continue_flag",
        nargs="?",
        choices=["continue"],
        help="Resume the latest running batch from its first unfinished file",
    )
    p_discover.add_argument(
        "--report-prefix",
        default="web-demo-run-all",
        help="Report filename prefix (default: web-demo-run-all)",
    )
    p_discover.add_argument(
        "--filter-file",
        type=Path,
        default=None,
        help=(
            "Path to a file listing test files relative to demo/e2e/, one per line. "
            "Blank lines and lines starting with # are skipped."
        ),
    )
    p_discover.set_defaults(func=cmd_discover)

    p_checkpoint = sub.add_parser(
        "checkpoint",
        help="Mark the next file as current in the batch JSON.",
    )
    p_checkpoint.add_argument("--json", type=Path, required=True)
    p_checkpoint.add_argument("--index", type=int, required=True)
    p_checkpoint.set_defaults(func=cmd_checkpoint)

    p_record = sub.add_parser(
        "record",
        help="Append the current file result and advance the checkpoint.",
    )
    p_record.add_argument("--json", type=Path, required=True)
    p_record.add_argument("--status", choices=["passed", "failed"], required=True)
    p_record.add_argument("--exit-code", type=int, default=0)
    p_record.add_argument("--duration", type=float, default=0.0)
    p_record.add_argument("--run-id", default="")
    p_record.add_argument("--logs", default="")
    p_record.add_argument("--error", default="")
    p_record.add_argument("--fixed", action="store_true")
    p_record.set_defaults(func=cmd_record)

    p_block = sub.add_parser(
        "block",
        help="Record a blocking error without advancing the current file.",
    )
    p_block.add_argument("--json", type=Path, required=True)
    p_block.add_argument("--error", required=True)
    p_block.set_defaults(func=cmd_block)

    p_scan = sub.add_parser(
        "scan",
        help=(
            "Manage the scan_results[] phase used by /t-tools:t-web-demo-run-all scan. "
            "Without --file, (re)initialize scan_results for every discovered "
            "file. With --file, record one file's fast-mode outcome."
        ),
    )
    p_scan.add_argument("--json", type=Path, required=True)
    p_scan.add_argument(
        "--file",
        default="",
        help="Test file to record (repo-relative posix). Omit to initialize.",
    )
    p_scan.add_argument("--status", choices=["passed", "failed"], default="passed")
    p_scan.add_argument("--exit-code", type=int, default=0)
    p_scan.add_argument("--duration", type=float, default=0.0)
    p_scan.add_argument("--run-id", default="")
    p_scan.add_argument("--logs", default="")
    p_scan.add_argument(
        "--force",
        action="store_true",
        help="Reinitialize scan_results even when already populated.",
    )
    p_scan.add_argument(
        "--scan-run-id",
        default="",
        help="Optional explicit scan run ID (default: run-all-scan-<ts>).",
    )
    p_scan.set_defaults(func=cmd_scan)

    p_cluster = sub.add_parser(
        "cluster",
        help=(
            "Read failing runs' Playwright logs and group failures by "
            "normalized error fingerprint. Operates on scan_results, falling "
            "back to entries. Prints one JSON line on stdout."
        ),
    )
    p_cluster.add_argument("--json", type=Path, required=True)
    p_cluster.set_defaults(func=cmd_cluster)

    p_finalize = sub.add_parser(
        "finalize",
        help="Render Markdown report from batch JSON and mark batch completed.",
    )
    p_finalize.add_argument(
        "--json",
        type=Path,
        required=True,
        help="Path to the batch JSON report (absolute or relative to repo root).",
    )
    p_finalize.set_defaults(func=cmd_finalize)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not getattr(args, "command", None):
        # No subcommand: do NOT execute any batch. The old default mode spawned
        # nested `claude -p` subprocesses and locked the parent session for up
        # to hours. Direct batch execution must go through /t-tools:t-web-demo-run-all.
        parser.print_help()
        print("")
        print("Direct batch execution is driven by /t-tools:t-web-demo-run-all in the")
        print("main session. Run `/t-tools:t-web-demo-run-all` (fresh) or")
        print("`/t-tools:t-web-demo-run-all continue` (resume). This script only provides discovery,")
        print("checkpoint persistence, and reporting helpers.")
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
