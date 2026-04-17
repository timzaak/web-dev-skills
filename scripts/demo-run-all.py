#!/usr/bin/env python3
"""
Batch runner for all Demo E2E files.

Runs demo files sequentially via scripts/demo-test-runner.py, preserves
the single-environment / single-file contract, and writes both Markdown and
JSON summaries for later diagnosis.

Supports two modes:
  - fresh (default): run from beginning
  - continue: resume from last interrupted or failed file
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
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
EXCLUDED_DIR_NAMES = {"fixtures", "templates", "verification"}


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run all Demo E2E files sequentially (using Claude CLI by default)"
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["continue"],
        help="Resume the latest batch from the interrupted file or latest failed file",
    )
    parser.add_argument(
        "--report-prefix",
        default="demo-run-all",
        help="Report filename prefix (default: demo-run-all)",
    )
    parser.add_argument(
        "--log-level",
        default="mini",
        choices=["mini", "verbose"],
        help="Log level for test execution",
    )
    parser.add_argument(
        "--direct-script",
        action="store_true",
        help="Use direct demo-test-runner.py script instead of Claude CLI (fallback mode)",
    )
    return parser


def discover_test_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(E2E_DIR.rglob("*.e2e.ts")):
        rel = path.relative_to(E2E_DIR)
        if any(part in EXCLUDED_DIR_NAMES for part in rel.parts):
            continue
        if "test-" in path.name:
            continue
        files.append(path)
    return files


def print_header(text: str) -> None:
    print(f"\n{'='*60}", flush=True)
    print(f"  {text}", flush=True)
    print(f"{'='*60}\n", flush=True)


def print_step(step: str, details: str = "") -> None:
    if details:
        print(f"[demo-run-all] {step}: {details}", flush=True)
    else:
        print(f"[demo-run-all] {step}", flush=True)


def now_display() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


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
    direct_script: bool,
) -> dict[str, object]:
    return {
        "generated_at": now_display(),
        "updated_at": now_display(),
        "report_prefix": report_prefix,
        "batch_status": "running",
        "mode": "direct-script" if direct_script else "claude-cli",
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
    direct_script: bool,
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
    payload["mode"] = "direct-script" if direct_script else "claude-cli"
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


def check_claude_cli() -> bool:
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def extract_json_from_claude_output(stdout: str) -> dict[str, object]:
    import re
    json_pattern = r'Result:\s*(\{[^{}]*"success"[^{}]*\})'
    matches = re.findall(json_pattern, stdout)
    if matches:
        try:
            return json.loads(matches[-1])
        except json.JSONDecodeError:
            pass
    return {}


def extract_result(stdout: str) -> dict[str, object]:
    for line in reversed(stdout.splitlines()):
        if not line.startswith("Result: "):
            continue
        try:
            return json.loads(line[len("Result: ") :].strip())
        except json.JSONDecodeError:
            break
    return {}


def run_single(test_file: Path, *, log_level: str, batch_run_id: str) -> RunEntry:
    rel_path = test_file.relative_to(REPO_ROOT).as_posix()
    per_file_run_id = f"{batch_run_id}-{test_file.stem}"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "demo-test-runner.py"),
        rel_path,
        "--mode",
        "fast",
        "--log-level",
        log_level,
        "--run-id",
        per_file_run_id,
    ]
    started = time.time()

    stdout_lines = []
    with subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    ) as proc:
        for line in iter(proc.stdout.readline, ""):
            if line:
                stdout_lines.append(line)
                print(line, end="", flush=True)
        proc.wait()

    duration = round(time.time() - started, 1)
    stdout = "".join(stdout_lines)
    summary = extract_result(stdout)
    logs = str(summary.get("logs", ""))
    status = "passed" if proc.returncode == 0 else "failed"
    error = ""
    if proc.returncode != 0 and not logs:
        tail = "\n".join(stdout.splitlines()[-20:]).strip()
        error = tail or "demo-test-runner did not emit Result JSON"
    return RunEntry(
        test_file=rel_path,
        status=status,
        exit_code=proc.returncode,
        duration=duration,
        run_id=str(summary.get("runId", per_file_run_id)),
        logs=logs,
        summary=summary,
        error=error,
    )


def run_single_claude(test_file: Path, *, log_level: str, batch_run_id: str) -> RunEntry:
    """Use Claude CLI to call /t-demo-run (default behavior)"""
    rel_path = test_file.relative_to(REPO_ROOT).as_posix()
    per_file_run_id = f"{batch_run_id}-{test_file.stem}"

    cmd = [
        "claude",
        "--dangerously-skip-permissions",
        "-p",
        f"/t-demo-run {rel_path}",
    ]

    started = time.time()
    stdout_lines = []

    with subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    ) as proc:
        for line in iter(proc.stdout.readline, ""):
            if line:
                stdout_lines.append(line)
                print(line, end="", flush=True)
        proc.wait()

    duration = round(time.time() - started, 1)
    stdout = "".join(stdout_lines)
    summary = extract_json_from_claude_output(stdout)

    status = "passed" if summary.get("success") == "true" else "failed"
    logs = summary.get("logs", "")
    error = summary.get("error", "")
    is_fixed = summary.get("fixed", "false") == "true"

    return RunEntry(
        test_file=rel_path,
        status=status,
        exit_code=summary.get("exit_code", proc.returncode),
        duration=duration,
        run_id=summary.get("run_id", per_file_run_id),
        logs=logs,
        summary=summary,
        error=error,
        fixed=is_fixed,
    )


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


def main() -> int:
    args = build_parser().parse_args()
    test_files = discover_test_files()
    if not test_files:
        print("ERROR: No demo test files found")
        return 1

    if not args.direct_script and not check_claude_cli():
        print("WARNING: 'claude' command not found, falling back to direct script mode")
        print("         Install Claude Code CLI to use the enhanced mode with auto-fix")
        args.direct_script = True

    is_continue = args.command == "continue"

    ensure_quality_dir()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    if is_continue:
        try:
            payload, json_report_path, md_report_path, test_files, resume_index = restore_payload_for_continue(
                report_prefix=args.report_prefix,
                direct_script=args.direct_script,
            )
        except ValueError as exc:
            print(f"ERROR: {exc}")
            return 1
        batch_run_id = Path(str(json_report_path.stem)).name
        resumed_from = test_files[resume_index].relative_to(REPO_ROOT).as_posix()
    else:
        json_report_path = QUALITY_DIR / f"{args.report_prefix}-{timestamp}.json"
        md_report_path = QUALITY_DIR / f"{args.report_prefix}-{timestamp}.md"
        payload = build_fresh_payload(
            report_prefix=args.report_prefix,
            test_files=test_files,
            json_report_path=json_report_path,
            md_report_path=md_report_path,
            direct_script=args.direct_script,
        )
        write_json_report(json_report_path, payload)
        batch_run_id = f"run-all-{timestamp}"
        resume_index = 0
        resumed_from = ""

    print_header("Demo E2E Batch Run")
    print(f"  Discovered: {len(test_files)} test files", flush=True)
    print(f"  Log level: {args.log_level}", flush=True)
    print(f"  Report prefix: {args.report_prefix}", flush=True)
    print(f"  Mode: {'Direct Script' if args.direct_script else 'Claude CLI (with auto-fix)'}", flush=True)
    print(f"  Invocation: {'Continue' if is_continue else 'Fresh'}", flush=True)
    print(f"  JSON report: {json_report_path.relative_to(REPO_ROOT).as_posix()}", flush=True)
    if resumed_from:
        print(f"  Resume from: {resumed_from}", flush=True)
    print(flush=True)

    entries = [
        RunEntry(
            test_file=str(entry["test_file"]),
            status=str(entry["status"]),
            exit_code=int(entry["exit_code"]),
            duration=float(entry["duration"]),
            run_id=str(entry["run_id"]),
            logs=str(entry.get("logs", "")),
            summary=entry.get("summary", {}) if isinstance(entry.get("summary", {}), dict) else {},
            error=str(entry.get("error", "")),
            fixed=parse_boolish(entry.get("fixed", False)),
        )
        for entry in payload.get("entries", [])
        if isinstance(entry, dict)
    ]
    started = time.time()

    print_header("Running Tests")
    for zero_based_index, test_file in enumerate(test_files[resume_index:], start=resume_index):
        rel_path = test_file.relative_to(REPO_ROOT).as_posix()
        display_index = zero_based_index + 1

        print(f"[{display_index}/{len(test_files)}] {rel_path}", flush=True)
        payload["current_index"] = zero_based_index
        payload["current_file"] = rel_path
        payload["entries"] = [asdict(entry) for entry in entries]
        payload["total_duration"] = round(time.time() - started, 1)
        write_json_report(json_report_path, payload)

        if args.direct_script:
            entry = run_single(test_file, log_level=args.log_level, batch_run_id=batch_run_id)
        else:
            entry = run_single_claude(test_file, log_level=args.log_level, batch_run_id=batch_run_id)

        entries.append(entry)
        payload["entries"] = [asdict(item) for item in entries]
        payload["current_index"] = zero_based_index + 1
        payload["current_file"] = ""
        payload["passed_files"] = sum(1 for item in entries if item.status == "passed")
        payload["failed_files"] = len(entries) - int(payload["passed_files"])
        payload["total_duration"] = round(time.time() - started, 1)
        write_json_report(json_report_path, payload)

        if entry.status == "passed":
            status_icon = "[PASS]"
        elif entry.fixed:
            status_icon = "[FIXED]"
        else:
            status_icon = "[FAIL]"

        print(f"       {status_icon} ({entry.duration}s)", flush=True)
        print(flush=True)

    total_duration = round(time.time() - started, 1)
    passed_count = sum(1 for entry in entries if entry.status == "passed")
    failed_count = len(entries) - passed_count

    print_header("Run Summary")
    print(f"  Total files: {len(entries)}", flush=True)
    print(f"  Passed: {passed_count}", flush=True)
    print(f"  Failed: {failed_count}", flush=True)
    print(f"  Duration: {total_duration}s", flush=True)
    print(flush=True)

    print_step("Generating reports...")
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

    print_step("Reports generated")
    print(f"  Markdown: {md_report_path.relative_to(REPO_ROOT).as_posix()}", flush=True)
    print(f"  JSON: {json_report_path.relative_to(REPO_ROOT).as_posix()}", flush=True)
    print(flush=True)

    if failed_count == 0:
        print_header("[SUCCESS] All Tests Passed!")
    else:
        print_header(f"[FAILURE] {failed_count} Test(s) Failed")
    print(flush=True)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
