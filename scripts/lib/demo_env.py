"""Delegate Web Demo environment operations to target-project hooks."""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field

from .paths import REPO_ROOT


@dataclass
class HealthStatus:
    healthy: bool = False
    services: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def run_hook(name: str, timeout: int) -> tuple[bool, str]:
    hook = REPO_ROOT / "scripts" / name
    if not hook.is_file():
        return False, f"Missing project hook: scripts/{name}; configure project environment or use --no-auto-env."
    try:
        result = subprocess.run(
            [sys.executable, str(hook)], cwd=REPO_ROOT,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    return result.returncode == 0, (result.stderr or result.stdout).strip()


def check_environment_health() -> HealthStatus:
    # The hook owns the complete project-specific health definition.
    ok, detail = run_hook("demo-health.py", 15)
    return HealthStatus(healthy=ok, services={"project": "healthy" if ok else "unhealthy"}, errors=[] if ok else [detail])


def start_environment(logger, timeout: int = 60) -> bool:
    ok, detail = run_hook("demo-start.py", timeout)
    if not ok:
        logger.error(detail)
        return False
    status = check_environment_health()
    for error in status.errors:
        logger.error(error)
    return status.healthy


def stop_environment() -> bool:
    ok, detail = run_hook("demo-stop.py", 30)
    if not ok:
        print(detail, file=sys.stderr)
    return ok
