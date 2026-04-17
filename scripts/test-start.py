#!/usr/bin/env python
import os
import socket
import subprocess
import sys
import tempfile
import time

from lib import docker
from lib.net import is_port_open
from lib.paths import REPO_ROOT


def _ports_free() -> bool:
    ports = [15433, 6380, 16432]
    occupied = [port for port in ports if is_port_open("127.0.0.1", port)]
    if not occupied:
        return True
    print("ERROR: Occupied test ports:", ", ".join(str(p) for p in occupied))
    return False


def _start_pgdog() -> bool:
    """Start PgDog proxy container.

    Returns:
        True if PgDog started successfully, False otherwise.
    """
    print("Starting PgDog proxy...")

    # Check if pgdog port is free
    if is_port_open("127.0.0.1", 16432):
        print("Port 16432 already in use, stopping existing PgDog...")
        if docker.container_running("t-test-pgdog"):
            docker.stop_container("t-test-pgdog")
        if docker.container_exists("t-test-pgdog"):
            docker.rm_container("t-test-pgdog")

    # Create PgDog configuration
    # Note: PgDog connects to PostgreSQL via localhost:15433 (host.docker.internal on Windows/Mac)
    pgdog_config = """[general]
host = "0.0.0.0"
port = 6432
workers = 2
default_pool_size = 32
min_pool_size = 1
checkout_timeout = 30000
idle_timeout = 600000
healthcheck_timeout = 5000
healthcheck_interval = 10000

[[databases]]
name = "postgres"
host = "host.docker.internal"
port = 15433
database_name = "postgres"
user = "postgres"
password = "postgres"
pool_size = 32
min_pool_size = 1
"""

    # PgDog also requires users.toml for authentication
    users_config = """[[users]]
name = "postgres"
password = "postgres"
database = "postgres"
pooler_mode = "session"
pool_size = 32
min_pool_size = 1
"""

    # Write config to file in current directory for Docker compatibility
    config_path = os.path.join(REPO_ROOT, "pgdog-test.toml")
    with open(config_path, 'w') as f:
        f.write(pgdog_config)

    # Write users config to file
    users_path = os.path.join(REPO_ROOT, "users-test.toml")
    with open(users_path, 'w') as f:
        f.write(users_config)

    # Create Docker network if it doesn't exist
    subprocess.run(
        ["docker", "network", "create", "t-test-network"],
        capture_output=True,
    )

    # Convert path to Windows format for Docker volume mount (avoid Git Bash path conversion)
    # On Windows, Docker needs native Windows paths
    if os.name == 'nt':
        config_path_docker = config_path.replace('\\', '\\\\')
        users_path_docker = users_path.replace('\\', '\\\\')
    else:
        config_path_docker = config_path
        users_path_docker = users_path

    # Start PgDog container (mount both config files in working directory)
    # PgDog's working directory is /pgdog and it looks for pgdog.toml and users.toml by default
    if not docker.run_detached(
        [
            "--name",
            "t-test-pgdog",
            "--memory=256m",
            "--cpus=0.25",
            "--restart=unless-stopped",
            "--log-opt",
            "max-size=10m",
            "--log-opt",
            "max-file=3",
            "-e",
            "RUST_LOG=error",  # Reduce pgdog logging to errors only
            "-e",
            "RUST_BACKTRACE=0",  # Disable backtrace
            "-p",
            "16432:6432",
            "-v",
            f"{config_path_docker}:/pgdog/pgdog.toml",
            "-v",
            f"{users_path_docker}:/pgdog/users.toml",
            "ghcr.io/pgdogdev/pgdog:v0.1.35",
        ]
    ):
        print("ERROR: PgDog container failed to start")
        return False

    # Wait for PgDog to accept authenticated SQL traffic, not just TCP connections.
    for attempt in range(30):
        code, out = docker.exec_check(
            "t-test-postgres",
            [
                "psql",
                "postgresql://postgres:postgres@host.docker.internal:16432/postgres?sslmode=disable",
                "-c",
                "select 1",
            ],
        )
        if code == 0 and "1" in out:
            print("PgDog is ready")
            return True
        time.sleep(1)

    print("ERROR: PgDog failed to start")
    return False


def main() -> int:
    stop_result = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "test-stop.py")])
    if stop_result.returncode != 0:
        return stop_result.returncode

    if not _ports_free():
        return 1

    if docker.container_running("t-test-postgres"):
        docker.stop_container("t-test-postgres")
    if docker.container_exists("t-test-postgres"):
        docker.rm_container("t-test-postgres")

    # Note: Not using custom Docker network on Windows for compatibility
    # Containers will communicate via localhost port mappings instead

    if not docker.run_detached(
        [
            "--name",
            "t-test-postgres",
            "--memory=1g",
            "--cpus=0.5",
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
            "15433:5432",
            "postgres:18-alpine",
        ]
    ):
        print("ERROR: PostgreSQL test container failed to start")
        return 1

    if not docker.wait_pg_ready("t-test-postgres", "postgres"):
        print("ERROR: PostgreSQL test container failed to start")
        return 1

    if docker.container_running("t-test-redis"):
        docker.stop_container("t-test-redis")
    if docker.container_exists("t-test-redis"):
        docker.rm_container("t-test-redis")

    if not docker.run_detached(
        [
            "--name",
            "t-test-redis",
            "--memory=256m",
            "--cpus=0.25",
            "--restart=unless-stopped",
            "--log-opt",
            "max-size=10m",
            "--log-opt",
            "max-file=3",
            "-p",
            "6380:6379",
            "redis:8.4-alpine",
        ]
    ):
        print("ERROR: Redis test container failed to start")
        return 1

    if not docker.wait_redis_ready("t-test-redis"):
        print("ERROR: Redis test container failed to start")
        return 1

    # Start PgDog proxy
    if not _start_pgdog():
        return 1

    if not docker.wait_redis_ready("t-test-redis"):
        print("ERROR: Redis test container failed to start")
        return 1

    # Verify PgDog connectivity with a real SQL round-trip.
    code, out = docker.exec_check(
        "t-test-postgres",
        [
            "psql",
            "postgresql://postgres:postgres@host.docker.internal:16432/postgres?sslmode=disable",
            "-c",
            "select 1",
        ],
    )
    if code != 0 or "1" not in out:
        print("ERROR: PgDog verification failed")
        return 1

    print("Test environment is ready. PgDog=localhost:16432 Redis=localhost:6380")
    return 0


if __name__ == "__main__":
    sys.exit(main())
