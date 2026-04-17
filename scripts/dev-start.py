#!/usr/bin/env python
import subprocess
import sys

from lib import docker
from lib.cli import require_executable
from lib.paths import LOG_DIR, REPO_ROOT, ensure_dir
from lib.proc import spawn_background


def main() -> int:
    ensure_dir(LOG_DIR)
    backend_log = LOG_DIR / "backend.log"
    frontend_log = LOG_DIR / "frontend.log"

    if docker.container_exists("t-dev-postgres"):
        docker.rm_force_container("t-dev-postgres")
    if not docker.run_detached(
        [
            "--name",
            "t-dev-postgres",
            "-e",
            "POSTGRES_USER=postgres",
            "-e",
            "POSTGRES_PASSWORD=password",
            "-e",
            "POSTGRES_DB=t_db",
            "-p",
            "5432:5432",
            "postgres:18-alpine",
        ]
    ):
        print("ERROR: PostgreSQL container start failed")
        return 1
    if not docker.wait_pg_ready("t-dev-postgres", "postgres"):
        print("ERROR: PostgreSQL failed to start")
        return 1

    if docker.container_exists("t-dev-redis"):
        docker.rm_force_container("t-dev-redis")
    if not docker.run_detached(["--name", "t-dev-redis", "-p", "6379:6379", "redis:8.4-alpine"]):
        print("ERROR: Redis container start failed")
        return 1
    if not docker.wait_redis_ready("t-dev-redis"):
        print("ERROR: Redis failed to start")
        return 1

    cargo = require_executable("cargo")
    npm = require_executable("npm", windows_fallback="npm.cmd")

    spawn_background(
        name="dev-backend",
        command=[cargo, "run", "--bin", "backend-api"],
        cwd=REPO_ROOT / "backend",
        stdout_path=backend_log,
    )

    spawn_background(
        name="dev-frontend",
        command=[npm, "run", "dev"],
        cwd=REPO_ROOT / "frontend",
        stdout_path=frontend_log,
    )
    print(
        f"Development environment started. Frontend=http://localhost:3000 Backend=http://localhost:8080 "
        f"Logs={backend_log},{frontend_log}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
