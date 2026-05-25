#!/usr/bin/env python
import platform
import subprocess
import sys
import time

from lib import docker
from lib.net import is_port_open
from lib.paths import SCRIPTS_DIR


def _ports_free() -> bool:
    ports = [15433, 6380, 16432]
    occupied = [port for port in ports if is_port_open("127.0.0.1", port)]
    if not occupied:
        return True
    print("ERROR: Occupied test ports:", ", ".join(str(p) for p in occupied))
    return False


def _host_gateway_args() -> list[str]:
    if platform.system() == "Linux":
        return ["--add-host", "host.docker.internal:host-gateway"]
    return []


def _build_pgdog_bootstrap_command(pgdog_config: str, users_config: str) -> str:
    return f"""cat > /tmp/pgdog.toml <<'PGDOG_CONFIG'
{pgdog_config}
PGDOG_CONFIG
cat > /tmp/users.toml <<'USERS_CONFIG'
{users_config}
USERS_CONFIG
exec /usr/local/bin/pgdog -c /tmp/pgdog.toml -u /tmp/users.toml run
"""


def _print_pgdog_failure_diagnostics(last_probe_output: str) -> None:
    if last_probe_output:
        print(f"PgDog last probe output: {last_probe_output}")

    inspect = subprocess.run(
        [
            "docker",
            "inspect",
            "t-test-pgdog",
            "--format",
            "{{json .State}} {{json .Mounts}}",
        ],
        capture_output=True,
        text=True,
    )
    if inspect.returncode == 0 and inspect.stdout.strip():
        print(f"PgDog inspect: {inspect.stdout.strip()}")

    logs = subprocess.run(
        ["docker", "logs", "t-test-pgdog", "--tail", "50"],
        capture_output=True,
        text=True,
    )
    log_output = (logs.stdout or logs.stderr).strip()
    if log_output:
        print("PgDog logs:")
        print(log_output)


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

    # Create Docker network if it doesn't exist
    subprocess.run(
        ["docker", "network", "create", "t-test-network"],
        capture_output=True,
    )

    bootstrap_cmd = _build_pgdog_bootstrap_command(pgdog_config, users_config)
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
            *_host_gateway_args(),
            "-p",
            "16432:6432",
            "--entrypoint",
            "sh",
            "ghcr.io/pgdogdev/pgdog:v0.1.35",
            "-lc",
            bootstrap_cmd,
        ]
    ):
        print("ERROR: PgDog container failed to start")
        return False

    # Wait for PgDog to accept authenticated SQL traffic, not just TCP connections.
    last_probe_output = ""
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
        last_probe_output = out
        if code == 0 and "1" in out:
            print("PgDog is ready")
            return True
        time.sleep(1)

    print("ERROR: PgDog failed to start")
    _print_pgdog_failure_diagnostics(last_probe_output)
    return False


def main() -> int:
    stop_result = subprocess.run([sys.executable, str(SCRIPTS_DIR / "test-stop.py")])
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
            "--shm-size=512m",
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
            *_host_gateway_args(),
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

    print("Cleaning up leftover test schemas...")
    cleanup_cmd = [
        "docker",
        "exec",
        "t-test-postgres",
        "psql",
        "-U",
        "postgres",
        "-h",
        "localhost",
        "-d",
        "postgres",
        "-c",
        """DO $$
DECLARE
    schema_record RECORD;
BEGIN
    FOR schema_record IN
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'test_%' OR schema_name LIKE 'template_test_schema_%'
    LOOP
        EXECUTE 'DROP SCHEMA IF EXISTS "' || schema_record.schema_name || '" CASCADE';
        RAISE NOTICE 'Dropped schema: %', schema_record.schema_name;
    END LOOP;
END $$;""",
    ]
    result = subprocess.run(cleanup_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("[OK] Test schema cleanup completed")
    else:
        print(f"[WARN] Schema cleanup had issues: {result.stderr}")

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
