import subprocess
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import Logger


def _run(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["docker", *args], text=True, capture_output=True)


def container_exists(name: str) -> bool:
    result = _run(["ps", "-a", "--filter", f"name={name}", "--format", "{{.Names}}"], capture=True)
    return name in result.stdout.splitlines()


def container_running(name: str) -> bool:
    result = _run(["ps", "--filter", f"name={name}", "--format", "{{.Names}}"], capture=True)
    return name in result.stdout.splitlines()


def stop_container(name: str) -> None:
    _run(["stop", name])


def rm_force_container(name: str) -> None:
    _run(["rm", "-f", name])


def rm_container(name: str) -> None:
    _run(["rm", name])


def run_detached(args: list[str]) -> bool:
    result = _run(["run", "-d", *args])
    return result.returncode == 0


def exec_check(container: str, args: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        ["docker", "exec", container, *args],
        text=True, capture_output=True,
    )
    output = result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
    return result.returncode, output


def wait_pg_ready(container: str, user: str, attempts: int = 30, sleep_seconds: int = 2, logger: "Logger | None" = None) -> bool:
    """Wait for PostgreSQL to be ready.

    Args:
        container: Container name
        user: PostgreSQL user
        attempts: Maximum number of attempts
        sleep_seconds: Seconds to sleep between attempts
        logger: Optional logger for progress reporting

    Returns:
        True if PostgreSQL is ready, False otherwise
    """
    if logger and logger.level >= 2:
        logger.verbose_info(f"PostgreSQL to be ready...")

    start_time = time.time()
    for i in range(attempts):
        code, _ = exec_check(container, ["pg_isready", "-U", user])
        if code == 0:
            elapsed = time.time() - start_time
            if logger and logger.level >= 2:
                logger.verbose_info(f"PostgreSQL ready after {elapsed:.1f}s ({i + 1}/{attempts} attempts)")
            return True
        time.sleep(sleep_seconds)
        if logger and logger.level >= 2:
            elapsed = time.time() - start_time
            if (i + 1) % 5 == 0 or i == attempts - 1:
                logger.progress("PostgreSQL", i + 1, attempts)

    return False


def wait_redis_ready(container: str, attempts: int = 30, sleep_seconds: int = 2, logger: "Logger | None" = None) -> bool:
    """Wait for Redis to be ready.

    Args:
        container: Container name
        attempts: Maximum number of attempts
        sleep_seconds: Seconds to sleep between attempts
        logger: Optional logger for progress reporting

    Returns:
        True if Redis is ready, False otherwise
    """
    if logger and logger.level >= 2:
        logger.verbose_info(f"Redis to be ready...")

    start_time = time.time()
    for i in range(attempts):
        code, out = exec_check(container, ["redis-cli", "ping"])
        if code == 0 and out == "PONG":
            elapsed = time.time() - start_time
            if logger and logger.level >= 2:
                logger.verbose_info(f"Redis ready after {elapsed:.1f}s ({i + 1}/{attempts} attempts)")
            return True
        time.sleep(sleep_seconds)
        if logger and logger.level >= 2:
            elapsed = time.time() - start_time
            if (i + 1) % 5 == 0 or i == attempts - 1:
                logger.progress("Redis", i + 1, attempts)

    return False
