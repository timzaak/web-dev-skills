#!/usr/bin/env python
import argparse
import sys
import subprocess
import time
from pathlib import Path

from lib import docker
from lib.proc import kill_process_by_port
# Removed state file dependencies: terminate_from_state, wait_process_exit, load_state
from lib.paths import LOG_DIR


def should_print(quiet: bool) -> bool:
    """Helper function to determine if we should print based on quiet mode."""
    return not quiet


# Demo environment ports that may have node processes
DEMO_PORTS = [3000, 3001, 3002, 3003]
BACKEND_PORT = 8080
LOG_DELETE_RETRIES = 5
LOG_DELETE_RETRY_INTERVAL_SECONDS = 0.3
DEMO_LOG_FILES = [
    LOG_DIR / "backend-demo.log.out",
    LOG_DIR / "backend-demo.log.err",
    LOG_DIR / "frontend-demo.log.out",
    LOG_DIR / "frontend-demo.log.err",
]
# Skip all runtime files - they may be inaccurate
DEMO_RUNTIME_FILES: list[Path] = []

# Verbose mode flag (set by main())
verbose = False


def log_verbose(message: str) -> None:
    """Print message only in verbose mode."""
    if verbose:
        print(message)


def kill_demo_node_processes(quiet: bool) -> None:
    """Kill node processes occupying demo-related ports.

    This is a fallback when process state files are missing or corrupted.
    Only kills processes on ports 3000-3003 that are typically used by Vite dev servers.
    """
    killed_count = 0
    for port in DEMO_PORTS:
        log_verbose(f"Checking port {port}...")
        if kill_process_by_port(port):
            killed_count += 1
            log_verbose(f"Killed process on port {port}")
    if killed_count > 0 and should_print(quiet):
        print(f"Killed {killed_count} process(es) on demo ports")


def _pids_holding_path_windows(path: str) -> set[int]:
    """Return PIDs holding a file path by querying Sysinternals handle.exe on Windows.

    Disabled for Git Bash compatibility issues.
    """
    # Disabled: handle.exe has compatibility issues with Git Bash
    return set()


def kill_demo_log_holders(quiet: bool) -> None:
    """Best-effort cleanup for orphan processes still holding demo log files."""
    if sys.platform != "win32":
        return

    pids: set[int] = set()
    for log_file in DEMO_LOG_FILES:
        pids.update(_pids_holding_path_windows(str(log_file)))

    killed = 0
    for pid in sorted(pids):
        result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F", "/T"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            killed += 1

    if killed > 0 and should_print(quiet):
        print(f"Killed {killed} orphan process(es) holding demo logs")


def _delete_with_retry(path: Path) -> bool:
    """Delete file with retry for lock-contention scenarios."""
    for _ in range(LOG_DELETE_RETRIES):
        try:
            if not path.exists():
                return True
            log_verbose(f"Deleting file: {path}")
            path.unlink()
            return True
        except FileNotFoundError:
            return True
        except (PermissionError, OSError):
            time.sleep(LOG_DELETE_RETRY_INTERVAL_SECONDS)
    return not path.exists()


def cleanup_demo_files() -> tuple[list[Path], list[Path]]:
    """Delete demo runtime/log files and return (failed_runtime, failed_logs)."""
    failed_runtime: list[Path] = []
    failed_logs: list[Path] = []

    for path in DEMO_RUNTIME_FILES:
        if not _delete_with_retry(path):
            failed_runtime.append(path)

    for path in DEMO_LOG_FILES:
        if not _delete_with_retry(path):
            failed_logs.append(path)

    return failed_runtime, failed_logs


def main() -> int:
    parser = argparse.ArgumentParser(description="Stop the demo environment")
    parser.add_argument("--quiet", action="store_true", help="Suppress all output")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    quiet = args.quiet
    global verbose
    verbose = args.verbose

    # Step 1: Kill backend process by port 8080
    if should_print(quiet):
        print("Stopping backend...")
    log_verbose(f"Checking port {BACKEND_PORT} for backend process...")
    kill_process_by_port(BACKEND_PORT)
    log_verbose(f"Backend process on port {BACKEND_PORT} killed (if present)")

    # Step 2: Kill frontend processes by demo ports
    if should_print(quiet):
        print("Stopping frontend...")
    kill_demo_node_processes(quiet)

    # Step 3: Stop and remove Docker containers
    if should_print(quiet):
        print("Stopping containers...")
    containers_to_stop = ["t-demo-redis", "t-demo-postgres"]
    for container in containers_to_stop:
        if docker.container_exists(container):
            log_verbose(f"Stopping container: {container}")
            docker.stop_container(container)
        else:
            log_verbose(f"Container not found (already stopped): {container}")
    time.sleep(1.0)
    for container in containers_to_stop:
        if docker.container_exists(container):
            log_verbose(f"Removing container: {container}")
            docker.rm_force_container(container)

    # Step 4: Best-effort cleanup for orphan processes
    kill_demo_log_holders(quiet)

    # Step 5: Cleanup log files (optional, non-fatal)
    failed_logs = cleanup_demo_files()[1]
    if failed_logs and should_print(quiet):
        for failed in failed_logs:
            print(f"WARN: Failed to delete log file (can be cleaned later): {failed}")

    if should_print(quiet):
        print("Demo stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
