#!/usr/bin/env python
import sys

from lib import docker


def main() -> int:
    if docker.container_running("t-test-pgdog"):
        docker.stop_container("t-test-pgdog")
    if docker.container_exists("t-test-pgdog"):
        docker.rm_container("t-test-pgdog")

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


if __name__ == "__main__":
    sys.exit(main())
