#!/usr/bin/env python3
"""Check that task runner items cover their planned tests.

This is a planning gate. It does not execute tests. For Rust backend runners it
can ask cargo-nextest to list the tests selected by the documented command.
Frontend, miniapp, Flutter, and demo runners are checked statically because project scripts vary.
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


COMMAND_MARKERS = {
    "backend": "backend-test.py",
    "frontend": "npm run test",
    "miniapp": "npm run",
    "flutter": "",
    "demo": "demo-test-runner.py",
}

TEST_TOKEN_RE = re.compile(r"`([^`]+)`")
COMMAND_LINE_RE = re.compile(
    r"(?P<command>(?:uv\s+run\s+(?:\$\{CLAUDE_PLUGIN_ROOT\}/)?scripts/backend-test\.py|uv\s+run\s+(?:\$\{CLAUDE_PLUGIN_ROOT\}\\)?scripts\\backend-test\.py|"
    r"(?:cd\s+\S+\s+&&\s+)?npm\s+run\s+(?:test(?::run)?|typecheck|build(?::[A-Za-z0-9_-]+)?)|"
    r"(?:cd\s+\S+\s+&&\s+)?(?:flutter|fvm\s+flutter)\s+(?:test|analyze)|patrol\s+test|"
    r"uv\s+run\s+scripts/demo-test-runner\.py|uv\s+run\s+scripts\\demo-test-runner\.py)"
    r"[^\n`]*)"
)


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
    parts = [part.lower() for part in path.parts]
    for layer in ("backend", "frontend", "miniapp", "flutter", "demo"):
        if layer in parts:
            return layer
    return None


def find_runner_files(root: Path, feature: str, layer: str | None) -> list[Path]:
    task_root = root / ".ai" / "task" / feature
    if not task_root.is_dir():
        raise SystemExit(f"Task directory not found: {task_root}")

    layers = [layer] if layer else ["backend", "frontend", "miniapp", "flutter", "demo"]
    files: list[Path] = []
    for current_layer in layers:
        if current_layer == "demo":
            candidates = list((task_root / "demo").glob("*/*.md"))
        else:
            candidates = list((task_root / current_layer / "test").glob("*.md"))
        for path in candidates:
            content = read_text(path)
            lowered = content.lower()
            has_runner_type = re.search(r"test_item_type\W*(?:[:|]|\*\*:\s*)\W*runner\b", lowered) is not None
            has_layer_command = COMMAND_MARKERS.get(current_layer, "") in lowered
            if (
                has_runner_type
                or has_layer_command
                or "runner" in path.name.lower()
                or "run-" in path.name.lower()
            ):
                files.append(path)
    return sorted(set(files))


def section_text(content: str, heading: str) -> str | None:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$", content, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    start = match.end()
    next_heading = re.search(r"^##\s+", content[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(content)
    return content[start:end]


def is_probable_test_token(token: str) -> bool:
    token = token.strip()
    if not token:
        return False
    lower = token.lower()
    if any(part in token for part in ("/", "\\", ".md", ".rs", ".ts", ".tsx", ".py")):
        return False
    if lower.startswith(("uv ", "cd ", "npm ", "cargo ", "skills/")):
        return False
    if lower in {"backend", "frontend", "miniapp", "flutter", "demo", "authoring", "runner", "none"}:
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
        if marker and marker.replace("\\", "/") not in command.replace("\\", "/") and marker != "npm run":
            continue
        commands.append(command)
    return list(dict.fromkeys(commands))


def is_full_suite_command(command: str, layer: str) -> bool:
    normalized = " ".join(command.strip().split())
    if layer == "backend":
        return normalized in {
            "uv run scripts/backend-test.py --",
            "uv run scripts\\backend-test.py --",
        }
    if layer == "frontend":
        return re.fullmatch(r"(?:cd\s+\S+\s+&&\s+)?npm\s+run\s+test(?::run)?", normalized) is not None
    if layer == "miniapp":
        return re.fullmatch(r"(?:cd\s+\S+\s+&&\s+)?npm\s+run\s+build(?::\S+)?", normalized) is not None
    if layer == "flutter":
        return re.fullmatch(r"(?:cd\s+\S+\s+&&\s+)?(?:fvm\s+)?flutter\s+test", normalized) is not None
    if layer == "demo":
        return (
            "demo-test-runner.py demo/e2e/" in normalized
            or re.fullmatch(r"uv\s+run\s+scripts[/\\]demo-test-runner\.py", normalized) is not None
        )
    return False


def has_full_suite_reason(content: str) -> bool:
    lower = content.lower()
    return (
        "full-suite escalation" in lower
        or "full suite escalation" in lower
        or "全量" in content and ("原因" in content or "升级" in content)
        or "targeted scope is no longer reliable" in lower
    )


def parse_backend_nextest_args(command: str) -> list[str]:
    normalized = command.replace("\\", "/")
    try:
        parts = shlex.split(normalized, posix=True)
    except ValueError:
        parts = normalized.split()
    try:
        idx = next(i for i, part in enumerate(parts) if part.endswith("backend-test.py"))
    except StopIteration:
        return []
    rest = parts[idx + 1 :]
    if rest and rest[0] == "--":
        return rest[1:]
    return rest


def backend_command_errors(command: str) -> list[str]:
    normalized = command.replace("\\", "/")
    parts = normalized.split()
    errors: list[str] = []
    script_part = next((part for part in parts if part.endswith("scripts/backend-test.py")), "")
    if "${CLAUDE_PLUGIN_ROOT}" in normalized:
        errors.append(
            "Backend test command must use target project script path: "
            "uv run scripts/backend-test.py -- [filter]"
        )
    if script_part and not script_part == "scripts/backend-test.py":
        errors.append(
            "Backend test command must not use plugin-root or absolute script paths: "
            "uv run scripts/backend-test.py -- [filter]"
        )
    try:
        idx = next(i for i, part in enumerate(parts) if part.endswith("scripts/backend-test.py"))
    except StopIteration:
        return errors
    rest = parts[idx + 1 :]
    if not rest or rest[0] != "--":
        errors.append("Backend test command must include '--' after scripts/backend-test.py.")
    return errors


def list_backend_tests(root: Path, command: str) -> tuple[int, set[str], str]:
    backend_root = root / "backend"
    if not backend_root.is_dir():
        return 1, set(), f"backend directory not found: {backend_root}"
    args = parse_backend_nextest_args(command)
    cmd = ["cargo", "nextest", "list", "-T", "oneline", *args]
    result = subprocess.run(
        cmd,
        cwd=backend_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    selected: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("Compiling ") or line.startswith("Finished "):
            continue
        selected.add(line)
        selected.add(line.split()[-1])
        selected.add(line.split("::")[-1])
    return result.returncode, selected, result.stderr.strip()


def command_mentions_expected(command: str, expected: set[str], layer: str) -> set[str]:
    if layer == "backend":
        return set()
    command_lower = command.lower()
    return {test for test in expected if test.lower() in command_lower}


def check_runner(root: Path, path: Path, dynamic: bool) -> RunnerCheck:
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
        if layer == "backend":
            command_errors = backend_command_errors(command)
            errors.extend(command_errors)
        if is_full_suite_command(command, layer) and not has_full_suite_reason(content):
            errors.append(f"Full-suite command lacks escalation reason: {command}")

    if dynamic and layer == "backend" and commands:
        for command in commands:
            if backend_command_errors(command):
                continue
            if is_full_suite_command(command, layer):
                continue
            code, listed, stderr = list_backend_tests(root, command)
            if code != 0:
                errors.append(f"cargo nextest list failed for command: {command}")
                if stderr:
                    warnings.append(stderr)
                continue
            selected.update(listed)
        missing = {test for test in expected if test not in selected}
        if missing:
            errors.append("Expected backend tests not selected by runner command: " + ", ".join(sorted(missing)))
    elif layer in {"frontend", "miniapp", "flutter", "demo"} and expected and commands:
        mentioned: set[str] = set()
        for command in commands:
            mentioned.update(command_mentions_expected(command, expected, layer))
        if not mentioned:
            warnings.append(
                "Static check only: command does not mention individual expected tests. "
                "Use file/pattern/grep filters or document why a broader target is required."
            )

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
    parser.add_argument("--layer", choices=["backend", "frontend", "miniapp", "flutter", "demo"], help="Limit to one layer.")
    parser.add_argument("--runner-file", type=Path, action="append", help="Specific runner item file to check.")
    parser.add_argument("--no-dynamic", action="store_true", help="Skip dynamic backend cargo-nextest list checks.")
    args = parser.parse_args()

    root = args.project_root.resolve()
    if args.runner_file:
        files = [(path if path.is_absolute() else root / path).resolve() for path in args.runner_file]
    else:
        files = find_runner_files(root, args.feature, args.layer)

    if not files:
        print("No runner files found.")
        return 1

    checks = [check_runner(root, path, dynamic=not args.no_dynamic) for path in files]
    return print_report(root, checks)


if __name__ == "__main__":
    sys.exit(main())
