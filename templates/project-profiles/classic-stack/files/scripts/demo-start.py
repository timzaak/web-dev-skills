#!/usr/bin/env python
import argparse
import sys
from lib.paths import REPO_ROOT, ensure_dir
from lib import demo_env
from lib.logger import Logger, LogLevel


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start the CAS Demo environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/demo-start.py              # Normal mode (simple output)
  uv run scripts/demo-start.py -v           # Verbose mode (detailed logs)
  uv run scripts/demo-start.py -vv          # Debug mode (very detailed)
  uv run scripts/demo-start.py --profile    # Show timing summary at end
  uv run scripts/demo-start.py -q           # Quiet mode (errors only)
        """
    )

    # Verbosity options
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for verbose, -vv for debug)"
    )
    verbosity_group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode (errors only)"
    )

    # Performance options
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Startup timeout in seconds (default: 60)"
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Show detailed timing summary"
    )

    args = parser.parse_args()

    # Determine log level
    if args.quiet:
        level = LogLevel.QUIET
    elif args.verbose == 1:
        level = LogLevel.VERBOSE
    elif args.verbose >= 2:
        level = LogLevel.DEBUG
    else:
        level = LogLevel.NORMAL

    # Create logger with appropriate level
    logger = Logger(level=level, profile=args.profile)

    # Start environment with logger
    ensure_dir(REPO_ROOT / "log")
    success = demo_env.start_environment(
        logger=logger,
        timeout=args.timeout,
    )

    # Print timing summary if profiling
    if args.profile:
        logger.print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
