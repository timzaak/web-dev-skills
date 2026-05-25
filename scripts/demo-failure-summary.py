#!/usr/bin/env python
"""Parse a Playwright JSON report and output a concise failure summary."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def extract_failures(data: dict) -> list[dict]:
    failures: list[dict] = []
    for suite in data.get("suites", []):
        _walk_suite(suite, failures)
    return failures


def _walk_suite(suite: dict, failures: list[dict], parent_path: str = "") -> None:
    suite_title = suite.get("title", "")
    current_path = f"{parent_path} > {suite_title}" if parent_path else suite_title

    for spec in suite.get("specs", []):
        for test in spec.get("tests", []):
            for result in test.get("results", []):
                if result.get("status") != "failed":
                    continue
                failures.append(
                    {
                        "file": spec.get("file", ""),
                        "suite_path": current_path,
                        "test_title": spec.get("title", ""),
                        "error": result.get("error", {}).get("message", "")[:200],
                        "duration_ms": result.get("duration", 0),
                    }
                )

    for child in suite.get("suites", []):
        _walk_suite(child, failures, current_path)


def format_summary(failures: list[dict], stats: dict) -> str:
    total = stats.get("total", 0)
    passed = stats.get("passed", 0)
    failed = stats.get("failed", 0)
    skipped = stats.get("skipped", 0)

    lines = [f"## Demo Test Results: {passed}/{total} passed"]
    if failed:
        lines.append(f"**{failed} failed**, {skipped} skipped\n")
    else:
        lines.append("All tests passed.\n")

    if not failures:
        return "\n".join(lines)

    by_file: dict[str, list[dict]] = {}
    for failure in failures:
        by_file.setdefault(failure["file"], []).append(failure)

    lines.append("### Failed Tests\n")
    for file, tests in sorted(by_file.items()):
        lines.append(f"**{file}**")
        for test in tests:
            lines.append(f"- `{test['test_title']}`")
            first_line = str(test["error"]).split("\n")[0].strip()
            if first_line:
                lines.append(f"  > {first_line}")
        lines.append(f"  Re-run: `uv run scripts/demo-test-runner.py {file}`\n")

    files = sorted(set(failure["file"] for failure in failures))
    lines.append("### Re-run All Failed\n")
    lines.append("```bash")
    for file in files:
        lines.append(f"uv run scripts/demo-test-runner.py {file}")
    lines.append("```\n")
    return "\n".join(lines)


def _stats_from_report(data: dict) -> dict:
    if "stats" not in data:
        return {"total": len(data.get("suites", [])), "passed": 0, "failed": 0, "skipped": 0}
    stats = data["stats"]
    return {
        "total": stats.get("total", 0),
        "passed": stats.get("expected", 0),
        "failed": stats.get("unexpected", 0) + stats.get("flaky", 0),
        "skipped": stats.get("skipped", 0),
    }


def _output_summary(summary: str) -> None:
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        Path(step_summary).write_text(summary, encoding="utf-8")
    print(summary)


def main() -> int:
    check_only = "--check-only" in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

    if not args:
        print("Usage: python demo-failure-summary.py <results.json> [--check-only]")
        return 1

    report_path = Path(args[0])
    if not report_path.exists():
        _output_summary(
            "## Demo Test Results\n\n"
            "No Playwright JSON report found. Tests may have crashed before producing results.\n"
        )
        return 1

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Failed to parse report: {exc}")
        return 1

    failures = extract_failures(data)
    stats = _stats_from_report(data)
    stats["failed"] = max(stats["failed"], len(failures))

    if check_only:
        if failures:
            files = sorted(set(failure["file"] for failure in failures))
            print(f"FAILED: {len(failures)} test(s) in {len(files)} file(s)")
            for file in files:
                print(f"  - {file}")
            return 1
        return 0

    _output_summary(format_summary(failures, stats))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
