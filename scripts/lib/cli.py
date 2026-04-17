import os
import shutil
import subprocess
from pathlib import Path
from typing import Mapping


def run_cmd(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    check: bool = False,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=dict(env) if env else None,
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
    )


def require_executable(name: str, windows_fallback: str | None = None) -> str:
    path = shutil.which(name)
    if path:
        return path
    if windows_fallback and os.name == "nt":
        fallback = shutil.which(windows_fallback)
        if fallback:
            return fallback
    raise RuntimeError(f"Required executable not found: {name}")
