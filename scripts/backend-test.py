#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from lib.java_backend import backend_dir, detect_build_tool, gradle_command, maven_command
from lib.paths import BACKEND_TEST_LOG, REPO_ROOT, SCRIPTS_DIR, ensure_dir


TABLE_DDL_PATTERN = re.compile(r"\b(CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE)\b", re.IGNORECASE)


def normalize_args(args: list[str]) -> list[str]:
    if args and args[0] == "--":
        return args[1:]
    return args


def parse_backend_args(raw_args: list[str]) -> tuple[str | None, list[str]]:
    module: str | None = None
    remaining: list[str] = []
    index = 0
    while index < len(raw_args):
        arg = raw_args[index]
        if arg == "--module" and index + 1 < len(raw_args):
            module = raw_args[index + 1]
            index += 2
            continue
        remaining.append(arg)
        index += 1
    return module, remaining


def translate_test_args(tool: str, test_args: list[str]) -> list[str]:
    translated: list[str] = []
    index = 0
    while index < len(test_args):
        arg = test_args[index]
        if arg == "--tests" and index + 1 < len(test_args):
            pattern = test_args[index + 1]
            if tool == "maven":
                translated.append(f"-Dtest={pattern}")
            else:
                translated.extend(["--tests", pattern])
            index += 2
            continue
        translated.append(arg)
        index += 1
    return translated


def build_command(root: Path, module: str | None, test_args: list[str]) -> list[str]:
    tool = detect_build_tool(root)
    translated_args = translate_test_args(tool, test_args)
    if tool == "maven":
        goals = ["test"]
        if module:
            goals.extend(["-pl", module])
        goals.extend(translated_args)
        return maven_command(root, goals)

    tasks = ["test"]
    if module:
        tasks = [f":{module}:test"]
    tasks.extend(translated_args)
    return gradle_command(root, tasks)


def is_backend_test_file(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if "migrations" in parts:
        return False
    if path.suffix != ".java":
        return False
    return "test" in path.name.lower() or "test" in parts


def run_backend_test_ddl_guard(root: Path) -> int:
    violations: list[tuple[Path, int, str]] = []
    for path in root.rglob("*.java"):
        if not is_backend_test_file(path):
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(content.splitlines(), start=1):
            if TABLE_DDL_PATTERN.search(line):
                violations.append((path, line_no, line.strip()))

    if not violations:
        print("Backend test DDL guard passed")
        return 0

    print("ERROR: backend tests must not define table DDL directly.")
    print("Use migration-backed schema helpers instead of CREATE/ALTER/DROP TABLE in test code.")
    for path, line_no, line in violations:
        relative = path.relative_to(REPO_ROOT)
        print(f"  {relative}:{line_no}: {line}")
    return 1


def extract_failure_lines(log_content: str, limit: int = 30) -> list[str]:
    patterns = [
        r"\bFAILED\b",
        r"\bFAILURE\b",
        r"\bERROR\b",
        r"Compilation failure",
        r"BUILD FAILED",
        r"There (was|were) .* failure",
    ]
    lines: list[str] = []
    for line in log_content.splitlines():
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            lines.append(line)
            if len(lines) >= limit:
                break
    return lines


def print_failure_summary(test_result: subprocess.CompletedProcess[str], test_log: Path, retry_command: list[str]) -> None:
    log_content = test_log.read_text(encoding="utf-8", errors="replace")
    failure_lines = extract_failure_lines(log_content)

    print(f"Backend tests failed with exit code {test_result.returncode}")
    print(f"Log: {test_log}")
    if failure_lines:
        print("Failure summary:")
        for line in failure_lines:
            print(f"  {line}")
    else:
        print("Failure summary: no concise Java/JUnit failure lines extracted; inspect the log.")

    print("Inspect the log:")
    print(f"  tail -n 200 {test_log.as_posix()}")
    print(f"  rg -n -C 6 'FAILED|FAILURE|ERROR|Compilation failure|BUILD FAILED' {test_log.as_posix()}")
    print("Next steps:")
    print("  Please fix the failing tests first, then rerun:")
    print(f"  {' '.join(retry_command)}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Java Spring Boot backend tests with managed test environment. "
            "Use '--' to pass extra args to Maven or Gradle. "
            "Use '--module <name>' before test args for a multi-module backend."
        )
    )
    parser.add_argument("test_args", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    raw_args = normalize_args(args.test_args)
    module, test_args = parse_backend_args(raw_args)
    root = backend_dir(REPO_ROOT)

    ddl_guard = run_backend_test_ddl_guard(root)
    if ddl_guard != 0:
        return ddl_guard

    test_log = BACKEND_TEST_LOG
    ensure_dir(test_log.parent)
    test_cmd = build_command(root, module, test_args)
    test_env = os.environ.copy()
    test_env.setdefault("SPRING_PROFILES_ACTIVE", "test")
    test_env.setdefault("TEST_POSTGRES_HOST", "127.0.0.1")
    test_env.setdefault("TEST_POSTGRES_PORT", "16432")
    test_env.setdefault("TEST_REDIS_URL", "redis://127.0.0.1:6380/0")

    start = subprocess.run([sys.executable, str(SCRIPTS_DIR / "test-start.py")], cwd=REPO_ROOT)
    if start.returncode != 0:
        return start.returncode

    try:
        with test_log.open("w", encoding="utf-8") as fp:
            test_result = subprocess.run(
                test_cmd,
                cwd=root,
                stdout=fp,
                stderr=subprocess.STDOUT,
                text=True,
                env=test_env,
            )
    finally:
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "test-stop.py")], cwd=REPO_ROOT, check=False)

    if test_result.returncode != 0:
        print_failure_summary(test_result, test_log, test_cmd)
        return test_result.returncode

    print(f"Backend tests passed. Log: {test_log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
