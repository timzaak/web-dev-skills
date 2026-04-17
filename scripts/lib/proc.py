import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Mapping


def is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        # Use PowerShell Get-Process to avoid localization issues with tasklist
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            # Get-Process returns process info if found, empty if not found
            return bool(result.stdout.strip())
        # Fall back to os.kill probe if PowerShell fails
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def wait_process_exit(pid: int, timeout_seconds: float = 3.0) -> bool:
    """Wait for a process to fully exit.

    Args:
        pid: Process ID
        timeout_seconds: Maximum time to wait

    Returns:
        True if process has exited, False if timeout
    """
    if pid <= 0:
        return True

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not is_running(pid):
            return True
        time.sleep(0.1)

    return False


def spawn_background(
    *,
    name: str | None = None,  # Name is optional, used only for state file tracking
    command: list[str],
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    out = open(stdout_path, "w", encoding="utf-8")
    if stderr_path is None:
        err = subprocess.STDOUT
    else:
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        err = open(stderr_path, "w", encoding="utf-8")

    creationflags = 0
    kwargs: dict = {}
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(
        command,
        cwd=str(cwd),
        # Avoid background services inheriting the current terminal input handle.
        # Some tools (e.g., frontend dev servers) listen on stdin and can alter
        # console input behavior in the parent PowerShell session on Windows.
        stdin=subprocess.DEVNULL,
        stdout=out,
        stderr=err,
        env=dict(env) if env else None,
        text=True,
        creationflags=creationflags,
        **kwargs,
    )
    out.close()
    if stderr_path is not None and err is not subprocess.STDOUT:
        err.close()
    # Skip saving state to file - it may be inaccurate
    # save_state(name, proc.pid, command, cwd)
    return proc.pid


def _get_pids_by_port_windows_powershell(port: int) -> set[str]:
    """Get PIDs listening on a TCP port via PowerShell Get-NetTCPConnection."""
    command = (
        f"$conns = Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue; "
        "if ($conns) { $conns | ForEach-Object { $_.OwningProcess } }"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return set()

    if result.returncode != 0:
        return set()

    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().isdigit()
    }


def _get_pids_by_port_windows_netstat(port: int) -> set[str]:
    """Get PIDs listening on a TCP port by parsing netstat output."""
    try:
        result = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return set()

    if result.returncode != 0:
        return set()

    pids: set[str] = set()
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 4:
            continue

        proto = parts[0].upper()
        if not proto.startswith("TCP"):
            continue

        local_addr = parts[1]
        local_port_text = local_addr.rsplit(":", 1)[-1] if ":" in local_addr else ""
        if local_port_text != str(port):
            continue

        pid = parts[-1]
        if pid.isdigit():
            pids.add(pid)
    return pids


def _get_pids_by_port_windows(port: int) -> set[str]:
    """Best-effort PID discovery for a TCP port on Windows."""
    pids = _get_pids_by_port_windows_powershell(port)
    if pids:
        return pids
    return _get_pids_by_port_windows_netstat(port)


def kill_process_by_port(port: int) -> bool:
    """Kill the process occupying the specified TCP port.

    Returns True if at least one process was killed, False otherwise.
    """
    if os.name == "nt":
        pids = _get_pids_by_port_windows(port)
        killed = False
        for pid in pids:
            try:
                result = subprocess.run(
                    ["taskkill", "/PID", pid, "/F", "/T"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except (ValueError, FileNotFoundError, OSError):
                continue
            if result.returncode == 0:
                killed = True
        return killed

    for cmd in (["lsof", "-ti", f":{port}"], ["fuser", "-k", f"{port}/tcp"]):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue

        if result.returncode != 0:
            continue

        if cmd[0] == "lsof":
            pids = [pid.strip() for pid in result.stdout.splitlines() if pid.strip()]
            killed = False
            for pid in pids:
                kill_result = subprocess.run(
                    ["kill", "-9", pid],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if kill_result.returncode == 0:
                    killed = True
            return killed

        return True

    return False
