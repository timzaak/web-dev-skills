#!/usr/bin/env python3
"""
Discovery + reporting helper for batch Demo E2E runs.

This script is intentionally side-effect-free at execution time: it does NOT
run tests or spawn nested `claude` processes. The actual per-file loop, the
diagnose -> fix -> rerun repair cycle, and the demo-environment restart are
driven by the `/t-demo-run-all` skill in the main session. Driving the batch
from the main session (short, observable Bash/Agent calls with file-backed
checkpoints) replaces the old blocking `claude -p "/t-demo-run <file>"`
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

  (no subcommand)
      Print guidance. Direct batch execution must go through /t-demo-run-all.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from lib.paths import REPO_ROOT, SCRIPTS_DIR

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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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

    current_file = payload.get("current_file")
    if isinstance(current_file, str) and current_file:
        try:
            return discovered_files.index(current_file)
        except ValueError as exc:
            raise ValueError(f"current_file not found in discovered_files: {current_file}") from exc

    last_failed_index = -1
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError("Latest batch report contains a non-object entry")
        if str(entry.get("status", "")) == "failed":
            last_failed_index = index

    if last_failed_index >= 0:
        return last_failed_index

    return len(entries)


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

    payload["entries"] = entries[:resume_index]
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
        "# Demo Run All Report",
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
            "1. Running individual tests with verbose logging: `/t-demo-run [file]`",
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


# --------------------------------------------------------------------------- #
# Subcommand: finalize
# --------------------------------------------------------------------------- #

def cmd_finalize(args: argparse.Namespace) -> int:
    json_report_path = args.json
    if not json_report_path.is_absolute():
        json_report_path = REPO_ROOT / json_report_path
    if not json_report_path.exists():
        print(f"ERROR: batch JSON not found: {json_report_path}")
        return 1

    payload = load_json_report(json_report_path)
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        print("ERROR: batch JSON does not contain entries")
        return 1

    entries: list[RunEntry] = []
    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue
        entries.append(
            RunEntry(
                test_file=str(entry.get("test_file", "")),
                status=str(entry.get("status", "")),
                exit_code=int(entry.get("exit_code", 0) or 0),
                duration=float(entry.get("duration", 0.0) or 0.0),
                run_id=str(entry.get("run_id", "")),
                logs=str(entry.get("logs", "")),
                summary=entry.get("summary", {}) if isinstance(entry.get("summary", {}), dict) else {},
                error=str(entry.get("error", "")),
                fixed=parse_boolish(entry.get("fixed", False)),
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
        "total_files": len(entries),
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
            "Test execution is driven by /t-demo-run-all in the main session."
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
        help="Resume the latest batch from the interrupted file or latest failed file",
    )
    p_discover.add_argument(
        "--report-prefix",
        default="demo-run-all",
        help="Report filename prefix (default: demo-run-all)",
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
        # to hours. Direct batch execution must go through /t-demo-run-all.
        parser.print_help()
        print("")
        print("Direct batch execution is driven by the /t-demo-run-all skill in the")
        print("main session. To start a batch there, run `/t-demo-run-all` (fresh) or")
        print("`/t-demo-run-all continue` (resume). This script only provides discovery")
        print("and reporting helpers (the `discover` and `finalize` subcommands).")
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
