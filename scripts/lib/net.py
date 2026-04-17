import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import Logger


def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def wait_for_tcp(host: str, port: int, timeout_seconds: int, interval_seconds: float = 1.0, logger: "Logger | None" = None) -> bool:
    """Wait for a TCP port to become available.

    Args:
        host: Host address
        port: Port number
        timeout_seconds: Maximum time to wait
        interval_seconds: Time between checks
        logger: Optional logger for progress reporting

    Returns:
        True if port is available, False if timeout
    """
    if logger and logger.level >= 2:
        logger.verbose_info(f"{host}:{port} to be available...")

    deadline = time.time() + timeout_seconds
    start_time = time.time()
    check_count = 0

    while time.time() < deadline:
        if is_port_open(host, port):
            elapsed = time.time() - start_time
            if logger and logger.level >= 2:
                logger.verbose_info(f"{host}:{port} ready after {elapsed:.1f}s ({check_count} checks)")
            return True
        time.sleep(interval_seconds)
        check_count += 1

        if logger and logger.level >= 2:
            elapsed = time.time() - start_time
            if check_count % 10 == 0 or check_count == 1:
                logger.progress(f"{host}:{port}", check_count, int(timeout_seconds / interval_seconds))

    return False


def wait_for_http_ok(url: str, timeout_seconds: int, interval_seconds: float = 1.0, logger: "Logger | None" = None) -> bool:
    """Wait for an HTTP endpoint to return a 2xx or 3xx status.

    Args:
        url: URL to check
        timeout_seconds: Maximum time to wait
        interval_seconds: Time between checks
        logger: Optional logger for progress reporting

    Returns:
        True if endpoint is healthy, False if timeout
    """
    if logger and logger.level >= 2:
        logger.verbose_info(f"{url} to be healthy...")

    parsed = urllib.parse.urlparse(url)
    is_loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if is_loopback else None

    deadline = time.time() + timeout_seconds
    start_time = time.time()
    check_count = 0

    while time.time() < deadline:
        try:
            request = urllib.request.Request(url)
            response = opener.open(request, timeout=1) if opener else urllib.request.urlopen(request, timeout=1)
            with response as resp:
                if 200 <= resp.status < 400:
                    elapsed = time.time() - start_time
                    if logger and logger.level >= 2:
                        logger.verbose_info(f"{url} healthy after {elapsed:.1f}s ({check_count} checks)")
                    return True
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(interval_seconds)
        check_count += 1

        if logger and logger.level >= 2:
            elapsed = time.time() - start_time
            if check_count % 5 == 0 or check_count == 1:
                logger.progress(f"{url}", check_count, int(timeout_seconds / interval_seconds))

    return False
