#!/usr/bin/env python
import sys

from lib import docker


def main() -> int:
    if docker.container_running("t-dev-postgres"):
        docker.stop_container("t-dev-postgres")
    if docker.container_exists("t-dev-postgres"):
        docker.rm_container("t-dev-postgres")

    if docker.container_running("t-dev-redis"):
        docker.stop_container("t-dev-redis")
    if docker.container_exists("t-dev-redis"):
        docker.rm_container("t-dev-redis")

    print("Development environment stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
