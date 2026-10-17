#!/usr/bin/env python3
"""Check planned Web Demo manifests and runner commands statically; does not run tests."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


COMMAND_MARKERS = {"web-demo": "web-demo-test-runner.py"}
TEST_TOKEN_RE = re.compile(r"`([^`]+)`")
COMMAND_LINE_RE = re.compile(r"(?P<command>uv\s+run\s+(?:\$\{CLAUDE_PLUGIN_ROOT\}/)?(?:scripts[/\\])?web-demo-test-runner\.py[^\n`]*)")


@dataclass
class RunnerCheck:
    file: Path
    layer: str
    expected_tests: set[str]
    commands: list[str]
    selected_tests: set[str]
    errors: list[str]
    warnings: list[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def infer_layer(path: Path) -> str | None:
    return "web-demo" if "web-demo" in path.parts else None


def find_runner_files(root: Path, feature: str, layer: str | None) -> list[Path]:
    task_root = root / ".ai" / "task" / feature
    if not task_root.is_dir():
        raise SystemExit(f"Task directory not found: {task_root}")
    return sorted(path for path in (task_root / "web-demo" / "dev").glob("*.md")
                  if "web-demo-test-runner.py" in read_text(path))


def section_text(content: str, heading: str) -> str | None:
    match = re.search(rf"^(#{{2,3}})\s+{re.escape(heading)}\s*$", content, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    start = match.end()
    level = len(match.group(1))
    next_heading = re.search(rf"^#{{1,{level}}}\s+", content[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(content)
    return content[start:end]


def is_probable_test_token(token: str) -> bool:
    token = token.strip()
    if not token:
        return False
    lower = token.lower()
    if any(part in token for part in ("/", "\\", ".md", ".ts", ".tsx", ".py")):
        return False
    if lower.startswith(("uv ", "cd ", "npm ", "skills/")):
        return False
    if lower in {"web-demo", "authoring", "runner", "none"}:
        return False
    return bool(re.search(r"[A-Za-z0-9_\u4e00-\u9fff]", token))


def extract_expected_tests(content: str) -> set[str]:
    expected: set[str] = set()
    preferred = section_text(content, "Expected Test Manifest")
    source = preferred or section_text(content, "Authoring Products to Test") or content

    for token in TEST_TOKEN_RE.findall(source):
        if is_probable_test_token(token):
            expected.add(token.strip())

    # Fallback for markdown bullets like "- test_name" in existing runner files.
    if not expected:
        for line in source.splitlines():
            match = re.match(r"\s*[-*]\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", line)
            if match:
                expected.add(match.group(1))
    return expected


def extract_commands(content: str, layer: str) -> list[str]:
    marker = COMMAND_MARKERS.get(layer)
    commands: list[str] = []
    for match in COMMAND_LINE_RE.finditer(content):
        command = match.group("command").strip()
        if marker and marker.replace("\\", "/") not in command.replace("\\", "/"):
            continue
        commands.append(command)
    return list(dict.fromkeys(commands))


def is_full_suite_command(command: str, layer: str) -> bool:
    normalized = " ".join(command.strip().split())
    return (re.search(r"web-demo-test-runner\.py\s+demo/e2e/?(?:\s|$)", normalized) is not None
            or re.fullmatch(r"uv\s+run\s+scripts[/\\]web-demo-test-runner\.py", normalized) is not None)


def has_full_suite_reason(content: str) -> bool:
    lower = content.lower()
    return (
        "full-suite escalation" in lower
        or "full suite escalation" in lower
        or "全量" in content and ("原因" in content or "升级" in content)
        or "targeted scope is no longer reliable" in lower
    )


def check_runner(root: Path, path: Path) -> RunnerCheck:
    content = read_text(path)
    layer = infer_layer(path) or "unknown"
    expected = extract_expected_tests(content)
    commands = extract_commands(content, layer)
    selected: set[str] = set()
    errors: list[str] = []
    warnings: list[str] = []

    if not expected:
        errors.append("No expected tests found. Add an 'Expected Test Manifest' section.")
    if not commands:
        errors.append("No test runner command found.")

    for command in commands:
        if is_full_suite_command(command, layer) and not has_full_suite_reason(content):
            errors.append(f"Full-suite command lacks escalation reason: {command}")
    if expected and commands:
        warnings.append("Static planning check only; verify selected cases and runtime evidence in acceptance.")

    return RunnerCheck(path, layer, expected, commands, selected, errors, warnings)


def print_report(root: Path, checks: list[RunnerCheck]) -> int:
    failures = 0
    print("Test runner coverage check")
    print("=" * 60)
    for check in checks:
        if check.errors:
            failures += 1
        print(f"\n{normalize_path(check.file, root)} [{check.layer}]")
        print(f"  expected tests: {len(check.expected_tests)}")
        print(f"  commands: {len(check.commands)}")
        if check.selected_tests:
            print(f"  selected tests/list entries: {len(check.selected_tests)}")
        for command in check.commands:
            print(f"  command: {command}")
        for error in check.errors:
            print(f"  ERROR: {error}")
        for warning in check.warnings:
            print(f"  WARN: {warning}")
        if not check.errors:
            print("  PASS")
    print("\n" + "=" * 60)
    print(f"runner files checked: {len(checks)}")
    print(f"runner files with errors: {failures}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate task runner test coverage.")
    parser.add_argument("feature", help="Feature name under .ai/task/")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Target project root. Defaults to cwd.")
    parser.add_argument("--layer", choices=["web-demo"], help="Web Demo only.")
    parser.add_argument("--runner-file", type=Path, action="append", help="Specific runner item file to check.")
    args = parser.parse_args()

    root = args.project_root.resolve()
    if args.runner_file:
        files = [(path if path.is_absolute() else root / path).resolve() for path in args.runner_file]
    else:
        files = find_runner_files(root, args.feature, args.layer)

    if not files:
        print("No runner files found.")
        return 1

    checks = [check_runner(root, path) for path in files]
    return print_report(root, checks)


if __name__ == "__main__":
    sys.exit(main())
