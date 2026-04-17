#!/usr/bin/env python3
import argparse
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from lib.cli import require_executable
from lib import docker
from lib.net import is_port_open
from lib.paths import REPO_ROOT


def is_windows() -> bool:
    """Check if running on Windows"""
    return platform.system() == "Windows"


def is_macos() -> bool:
    """Check if running on macOS"""
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """Check if running on Linux"""
    return platform.system() == "Linux"


@dataclass
class ContainerSpec:
    name: str
    port: int
    run_args: list[str]
    ready_waiter: Callable[[str], bool]
    verify_cmd: list[str]
    verify_output: str | None = None
    start_error: str = "ERROR: Test container failed to start"
    verify_error: str = "ERROR: Test container verification failed"


@dataclass
class ContainerState:
    name: str
    created_by_script: bool = False
    reused_existing: bool = False


POSTGRES_SPEC = ContainerSpec(
    name="t-test-postgres",
    port=5433,
    run_args=[
        "--name",
        "t-test-postgres",
        "--memory=2g",
        "--restart=unless-stopped",
        "--log-opt",
        "max-size=10m",
        "--log-opt",
        "max-file=3",
        "-e",
        "POSTGRES_USER=postgres",
        "-e",
        "POSTGRES_PASSWORD=postgres",
        "-e",
        "POSTGRES_DB=postgres",
        "-p",
        "5433:5432",
        "postgres:18-alpine",
    ],
    ready_waiter=lambda name: docker.wait_pg_ready(name, "postgres"),
    verify_cmd=["pg_isready", "-U", "postgres"],
    start_error="ERROR: PostgreSQL test container failed to start",
    verify_error="ERROR: PostgreSQL verification failed",
)

REDIS_SPEC = ContainerSpec(
    name="t-test-redis",
    port=6380,
    run_args=[
        "--name",
        "t-test-redis",
        "--memory=512m",
        "--restart=unless-stopped",
        "--log-opt",
        "max-size=10m",
        "--log-opt",
        "max-file=3",
        "-p",
        "6380:6379",
        "redis:8.4-alpine",
    ],
    ready_waiter=docker.wait_redis_ready,
    verify_cmd=["redis-cli", "ping"],
    verify_output="PONG",
    start_error="ERROR: Redis test container failed to start",
    verify_error="ERROR: Redis verification failed",
)


def stop_test_environment() -> int:
    if docker.container_running("t-test-postgres"):
        docker.stop_container("t-test-postgres")
    if docker.container_exists("t-test-postgres"):
        docker.rm_container("t-test-postgres")

    if docker.container_running("t-test-redis"):
        docker.stop_container("t-test-redis")
    if docker.container_exists("t-test-redis"):
        docker.rm_container("t-test-redis")

    print("Backend test environment stopped")
    return 0


def ports_free(required_ports: list[int]) -> bool:
    occupied = [port for port in required_ports if is_port_open("127.0.0.1", port)]
    if not occupied:
        return True
    print("ERROR: Occupied test ports:", ", ".join(str(p) for p in occupied))
    return False


def cleanup_started_containers(states: list[ContainerState]) -> None:
    for state in states:
        if not state.created_by_script:
            continue
        if docker.container_running(state.name):
            docker.stop_container(state.name)
        if docker.container_exists(state.name):
            docker.rm_container(state.name)


def ensure_container(spec: ContainerSpec) -> tuple[int, ContainerState]:
    state = ContainerState(name=spec.name)

    if docker.container_running(spec.name):
        state.reused_existing = True
        return 0, state

    if docker.container_exists(spec.name):
        docker.rm_container(spec.name)

    if not ports_free([spec.port]):
        return 1, state

    if not docker.run_detached(spec.run_args):
        print(spec.start_error)
        return 1, state
    state.created_by_script = True

    if not spec.ready_waiter(spec.name):
        print(spec.start_error)
        return 1, state

    code, out = docker.exec_check(spec.name, spec.verify_cmd)
    if code != 0 or (spec.verify_output is not None and out != spec.verify_output):
        print(spec.verify_error)
        return 1, state

    return 0, state


def start_test_environment() -> tuple[int, list[ContainerState]]:
    command = [sys.executable, str(REPO_ROOT / "scripts" / "test-start.py")]
    result = subprocess.run(command, cwd=REPO_ROOT)
    return result.returncode, []


def build_nextest_command(nextest_args: list[str]) -> list[str]:
    # cargo is cross-platform (cargo.exe on Windows, cargo on macOS/Linux)
    cargo = require_executable("cargo")
    if nextest_args:
        return [cargo, "nextest", "run", *nextest_args]
    return [cargo, "nextest", "run", "--workspace"]


def print_utf8_safe(text: str) -> None:
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")


def format_command(args: list[str]) -> str:
    return subprocess.list2cmdline(args)


def normalize_nextest_args(nextest_args: list[str]) -> list[str]:
    if nextest_args and nextest_args[0] == "--":
        return nextest_args[1:]
    return nextest_args


def parse_semver(version_text: str) -> tuple[int, int, int] | None:
    match = re.search(r"cargo-nextest (\d+)\.(\d+)\.(\d+)", version_text)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


TABLE_DDL_PATTERN = re.compile(r"\b(CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE)\b", re.IGNORECASE)


def is_backend_test_file(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if "migrations" in parts:
        return False
    if path.suffix != ".rs":
        return False
    lower_name = path.name.lower()
    return "test" in lower_name or "tests" in parts


def run_backend_test_ddl_guard() -> int:
    backend_root = REPO_ROOT / "backend"
    violations: list[tuple[Path, int, str]] = []

    for path in backend_root.rglob("*.rs"):
        if not is_backend_test_file(path):
            continue

        content = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            if not TABLE_DDL_PATTERN.search(line):
                continue
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


def get_nextest_version() -> tuple[int, int, int] | None:
    cargo = require_executable("cargo")
    result = subprocess.run(
        [cargo, "nextest", "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return None
    return parse_semver(result.stdout)


def uses_rerun_latest(nextest_args: list[str]) -> bool:
    for index, arg in enumerate(nextest_args):
        if arg == "-R" and index + 1 < len(nextest_args) and nextest_args[index + 1] == "latest":
            return True
        if arg == "--rerun" and index + 1 < len(nextest_args) and nextest_args[index + 1] == "latest":
            return True
    return False


def ensure_rerun_supported(nextest_args: list[str]) -> int:
    if not uses_rerun_latest(nextest_args):
        return 0

    version = get_nextest_version()
    minimum = (0, 9, 123)
    if version is None:
        print("ERROR: Unable to determine cargo-nextest version for '-R latest' support.")
        print("       Install cargo-nextest 0.9.123 or newer.")
        return 2
    if version < minimum:
        actual = ".".join(str(part) for part in version)
        required = ".".join(str(part) for part in minimum)
        print(f"ERROR: cargo-nextest {actual} does not support '-R latest' or '--rerun latest'.")
        print(f"       Upgrade cargo-nextest to {required} or newer, then retry.")
        return 2
    return 0


def extract_failed_tests(log_content: str) -> list[str]:
    patterns = [
        r"^\s*FAIL\s+\[[^\]]+\]\s+\([^)]+\)\s+\S+\s+([\w:.-]+)\s*$",
        r"^\s*FAIL\s+\[[^\]]+\]\s+\([^)]+\)\s+([\w:.-]+)\s*$",
        r"^\s*FAILED\s+([\w:.-]+)\s*$",
        r"^\s*test\s+([\w:.-]+)\s+\.\.\.\s+FAILED\s*$",
    ]
    failed_tests: list[str] = []
    seen: set[str] = set()
    for line in log_content.splitlines():
        for pattern in patterns:
            match = re.search(pattern, line)
            if not match:
                continue
            test_name = match.group(1)
            if test_name not in seen:
                seen.add(test_name)
                failed_tests.append(test_name)
            break
    return failed_tests


def extract_compile_error_blocks(log_content: str, limit: int = 8) -> list[str]:
    lines = log_content.splitlines()
    blocks: list[str] = []
    seen: set[str] = set()
    i = 0

    while i < len(lines):
        line = lines[i]
        match = re.search(r"(error\[E\d+\]:.*)", line)
        if not match:
            i += 1
            continue

        header = re.sub(r"\x1b\[[0-9;]*m", "", match.group(1)).strip()
        detail = ""
        for look_ahead in range(i + 1, min(i + 6, len(lines))):
            candidate = re.sub(r"\x1b\[[0-9;]*m", "", lines[look_ahead]).strip()
            if "-->" in candidate:
                detail = candidate
                break
        key = f"{header}|{detail}"
        if key not in seen:
            seen.add(key)
            blocks.append(f"{header}\n  {detail}" if detail else header)
            if len(blocks) >= limit:
                break
        i += 1

    return blocks


def build_retry_commands(nextest_args: list[str], failed_tests: list[str]) -> list[str]:
    commands: list[str] = []
    rerun_latest = format_command(["uv", "run", "scripts/backend-test.py", "--", "-R", "latest"])
    commands.append(rerun_latest)

    base = ["uv", "run", "scripts/backend-test.py"]
    if nextest_args:
        base.extend(["--", *nextest_args])
        commands.append(format_command(base))

    filtered_args = [arg for arg in nextest_args if arg not in failed_tests]
    for test_name in failed_tests[:5]:
        commands.append(format_command(["uv", "run", "scripts/backend-test.py", "--", *filtered_args, test_name]))
    return list(dict.fromkeys(commands))


def print_failure_summary(test_result: subprocess.CompletedProcess[str], test_log: Path, nextest_args: list[str]) -> None:
    log_content = test_log.read_text(encoding="utf-8")
    failed_tests = extract_failed_tests(log_content)
    compile_error_blocks = extract_compile_error_blocks(log_content)
    fail_lines = len(re.findall(r"^\s*FAIL\s+\[[^\]]+\]", log_content, flags=re.MULTILINE))
    failed_test_count = max(len(failed_tests), fail_lines)
    compile_error_count = len(re.findall(r"error\[E\d+\]", log_content))
    retry_commands = build_retry_commands(nextest_args, failed_tests)
    failure_kind = "compile" if compile_error_count > 0 and failed_test_count == 0 else "test"

    print(f"Backend tests failed with exit code {test_result.returncode}")
    print(f"Log: {test_log}")
    print(f"Failure kind: {failure_kind}")
    print(f"Compilation errors: {compile_error_count}")
    print(f"Failed tests: {failed_test_count}")

    if compile_error_blocks:
        print("Compilation error summary:")
        for block in compile_error_blocks:
            print(f"  {block.replace(chr(10), chr(10) + '  ')}")
        remaining = compile_error_count - len(compile_error_blocks)
        if remaining > 0:
            print(f"  ... and {remaining} more compile errors in the log")

    if failed_tests:
        print("Failed test targets:")
        for test_name in failed_tests[:10]:
            print(f"  {test_name}")
        if len(failed_tests) > 10:
            print(f"  ... and {len(failed_tests) - 10} more")
    else:
        print("Failed test targets: not extracted from nextest output")

    print("Inspect the log:")
    print(f"  tail -n 200 {test_log.as_posix()}")
    print(f"  rg -n -C 6 'FAIL|FAILED|error\\[E' {test_log.as_posix()}")

    print("Next steps:")
    print("  Please fix the failing tests first, then rerun:")
    print("  uv run scripts/backend-test.py -- -R latest")
    print("  Ensure all previously failing tests now pass.")
    if len(retry_commands) > 1:
        print("  Additional retry commands:")
        for command in retry_commands[1:]:
            print(f"    {command}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run backend tests with managed test environment. "
            "Use '--' to pass extra args to 'cargo nextest run'."
        )
    )
    parser.add_argument(
        "nextest_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to 'cargo nextest run' after '--'.",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    nextest_args = normalize_nextest_args(args.nextest_args)
    rerun_support = ensure_rerun_supported(nextest_args)
    if rerun_support != 0:
        return rerun_support

    ddl_guard = run_backend_test_ddl_guard()
    if ddl_guard != 0:
        return ddl_guard

    test_log = REPO_ROOT / "backend-test-output.log"
    test_cmd = build_nextest_command(nextest_args)
    test_env = os.environ.copy()
    # Required by billing crypto tests
    test_env["ENCRYPTION_KEY"] = "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY="
    test_env["INTERNAL_API_KEY"] = "test-internal-api-key"
    test_env.setdefault("TEST_POSTGRES_HOST", "127.0.0.1")
    test_env.setdefault("TEST_POSTGRES_PORT", "16432")
    test_env.setdefault("TEST_REDIS_URL", "redis://127.0.0.1:6380/0")

    start_code, container_states = start_test_environment()
    if start_code != 0:
        return start_code

    try:
        with test_log.open("w", encoding="utf-8") as fp:
            test_result = subprocess.run(
                test_cmd,
                cwd=REPO_ROOT / "backend",
                stdout=fp,
                stderr=subprocess.STDOUT,
                text=True,
                env=test_env,
            )
    finally:
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "test-stop.py")],
            cwd=REPO_ROOT,
            check=False,
        )

    if test_result.returncode != 0:
        print_failure_summary(test_result, test_log, nextest_args)
        return test_result.returncode

    print(f"Backend tests passed. Log: {test_log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
