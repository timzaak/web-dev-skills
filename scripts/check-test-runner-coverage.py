#!/usr/bin/env python3
"""Check that task runner items cover their planned tests.

This is a planning gate. It does not execute tests. For Java/Maven backend
runners it statically enumerates the @Test methods selected by the documented
--module / --tests filter. Frontend, miniapp, Flutter, and demo runners are
checked statically because project scripts vary.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import shlex
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
    if any(part in token for part in ("/", "\\", ".md", ".java", ".ts", ".tsx", ".py")):
        return False
    if lower.startswith(("uv ", "cd ", "npm ", "mvn ", "skills/")):
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


def parse_backend_filter(command: str) -> tuple[str | None, list[str]]:
    """Return (module, test_patterns) parsed from a backend-test.py command."""
    normalized = command.replace("\\", "/")
    try:
        parts = shlex.split(normalized, posix=True)
    except ValueError:
        parts = normalized.split()
    try:
        idx = next(i for i, part in enumerate(parts) if part.endswith("backend-test.py"))
    except StopIteration:
        return None, []
    rest = parts[idx + 1 :]
    if rest and rest[0] == "--":
        rest = rest[1:]
    module: str | None = None
    patterns: list[str] = []
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--module" and i + 1 < len(rest):
            module = rest[i + 1]
            i += 2
            continue
        if arg == "--tests" and i + 1 < len(rest):
            patterns.append(rest[i + 1])
            i += 2
            continue
        if arg.startswith("-"):
            i += 1
            continue
        patterns.append(arg)  # bare positional filter, e.g. a test name
        i += 1
    return module, patterns


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


MODIFIER_TOKENS = {
    "public", "protected", "private", "static", "final", "default",
    "synchronized", "abstract", "native", "strictfp", "transient",
    "volatile", "void", "class", "interface", "enum", "record",
    "return", "new", "throws",
}

CLASS_DECL_RE = re.compile(r"\b(?:class|interface|enum|record)\s+(\w+)")


def backend_root_for(root: Path) -> Path:
    nested = root / "backend"
    if (nested / "pom.xml").is_file():
        return nested
    if (root / "pom.xml").is_file():
        return root
    return nested


def is_backend_test_source(path: Path) -> bool:
    if path.suffix != ".java":
        return False
    parts = {part.lower() for part in path.parts}
    if "migrations" in parts:
        return False
    return "test" in path.name.lower() or "test" in parts


def method_name_after_annotation(tail: str) -> str | None:
    stripped = re.sub(r"@\w+(?:\s*\([^)]*\))?", " ", tail)
    paren = stripped.find("(")
    if paren == -1:
        return None
    ids = re.findall(r"[A-Za-z_]\w*", stripped[:paren])
    return ids[-1] if ids else None


def extract_java_tests(content: str) -> tuple[str | None, list[str]]:
    match = CLASS_DECL_RE.search(content)
    class_name = match.group(1) if match else None
    methods: list[str] = []
    for token in re.finditer(r"@Test\b", content):
        name = method_name_after_annotation(content[token.end():token.end() + 300])
        if name and name not in MODIFIER_TOKENS:
            methods.append(name)
    return class_name, methods


def expand_filter_patterns(patterns: list[str]) -> list[tuple[str, str | None]]:
    pieces: list[tuple[str, str | None]] = []
    for pattern in patterns:
        for raw in pattern.split(","):
            raw = raw.strip()
            if not raw:
                continue
            cls_glob: str = raw
            meth_glob: str | None = None
            if "#" in raw:
                cls_glob, meth_glob = raw.split("#", 1)
            elif "*" in raw:
                # Java docs also use '.' as a method separator, e.g. *FooTest.createSuccess
                star = raw.rfind("*")
                dot = raw.find(".", star + 1)
                if dot != -1:
                    cls_glob, meth_glob = raw[:dot], raw[dot + 1:]
            pieces.append((cls_glob.strip(), meth_glob.strip() if meth_glob else None))
    return pieces


def glob_matches(value: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(value.lower(), pattern.lower())


def list_backend_tests(root: Path, command: str) -> tuple[int, set[str], str]:
    """Statically enumerate the Java @Test methods a backend-test.py command selects.

    Maven/Surefire has no native 'list tests' mode, so this scans backend test
    sources and applies the command's --module / --tests filter. Returns
    (exit_code, selected_names, note).
    """
    backend_root = backend_root_for(root)
    if not backend_root.is_dir():
        return 1, set(), f"backend directory not found: {backend_root}"

    module, patterns = parse_backend_filter(command)
    class_methods: dict[str, set[str]] = {}
    for path in backend_root.rglob("*.java"):
        if not is_backend_test_source(path):
            continue
        if module and module not in path.parts:
            continue
        class_name, methods = extract_java_tests(read_text(path))
        if class_name:
            class_methods.setdefault(class_name, set()).update(methods)

    selected: set[str] = set()
    pieces = expand_filter_patterns(patterns)
    if not pieces:
        for cls, methods in class_methods.items():
            selected.add(cls)
            selected.update(methods)
    else:
        for cls_glob, meth_glob in pieces:
            for cls, methods in class_methods.items():
                if not glob_matches(cls, cls_glob):
                    continue
                selected.add(cls)
                if meth_glob is None:
                    selected.update(methods)
                else:
                    for meth in methods:
                        if glob_matches(meth, meth_glob):
                            selected.add(meth)
                            selected.add(f"{cls}.{meth}")
    return 0, selected, ""


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
                errors.append(f"backend test listing failed for command: {command}")
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
    parser.add_argument("--no-dynamic", action="store_true", help="Skip dynamic backend test-listing checks.")
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
