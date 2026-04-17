"""Logging and timing module for diagnostic output."""

import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Callable, Self


class LogLevel(IntEnum):
    """Log verbosity levels."""
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


@dataclass
class TimingEntry:
    """A single timing entry for profiling."""
    name: str
    duration: float
    start_time: float
    end_time: float
    parent: str | None = None


@dataclass
class ProgressState:
    """State for progress tracking."""
    total: int
    current: int
    start_time: float
    name: str


class Logger:
    """Logger with timing and progress tracking capabilities."""

    def __init__(self, level: LogLevel = LogLevel.NORMAL, profile: bool = False):
        """Initialize logger.

        Args:
            level: Verbosity level (QUIET, NORMAL, VERBOSE, DEBUG)
            profile: Enable detailed timing profiling
        """
        self._level = level
        self._profile = profile
        self._timings: list[TimingEntry] = []
        self._stack: list[TimingEntry] = []
        self._start_time = time.time()
        self._output = sys.stdout

    @property
    def level(self) -> LogLevel:
        """Get current log level."""
        return self._level

    @property
    def profile(self) -> bool:
        """Get profile mode."""
        return self._profile

    def set_level(self, level: LogLevel) -> None:
        """Set log level."""
        self._level = level

    def quiet(self) -> Self:
        """Set to quiet mode and return self for chaining."""
        self.set_level(LogLevel.QUIET)
        return self

    def verbose(self) -> Self:
        """Set to verbose mode and return self for chaining."""
        self.set_level(LogLevel.VERBOSE)
        return self

    def debug(self) -> Self:
        """Set to debug mode and return self for chaining."""
        self.set_level(LogLevel.DEBUG)
        return self

    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on current level."""
        return self._level >= level

    def _format_timestamp(self) -> str:
        """Format current timestamp."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def _log(self, level: LogLevel, prefix: str, message: str) -> None:
        """Write log message to output."""
        if not self._should_log(level):
            return

        if self._level >= LogLevel.VERBOSE:
            timestamp = self._format_timestamp()
            self._output.write(f"[{timestamp}] {prefix}: {message}\n")
        else:
            # Simple format for NORMAL mode
            self._output.write(f"{message}\n")
        self._output.flush()

    def info(self, message: str) -> None:
        """Log info message."""
        self._log(LogLevel.NORMAL, "INFO", message)

    def verbose_info(self, message: str) -> None:
        """Log verbose info message (only in VERBOSE or DEBUG mode)."""
        self._log(LogLevel.VERBOSE, "INFO", message)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, "DEBUG", message)

    def warning(self, message: str) -> None:
        """Log warning message (always shown except QUIET)."""
        self._log(LogLevel.NORMAL, "WARNING", message)

    def error(self, message: str) -> None:
        """Log error message (always shown)."""
        self._log(LogLevel.NORMAL, "ERROR", message)

    def progress(self, name: str, current: int, total: int) -> None:
        """Show progress update."""
        if not self._should_log(LogLevel.VERBOSE):
            return

        elapsed = time.time() - self._start_time
        self._output.write(f"[{self._format_timestamp()}] DEBUG:     {name}... {current}/{total} ({elapsed:.1f}s elapsed)\n")
        self._output.flush()

    @contextmanager
    def timed(self, name: str):
        """Context manager to time a block of code.

        Usage:
            with logger.timed("doing something"):
                do_something()

        Args:
            name: Name for the timing entry
        """
        start = time.time()
        parent = self._stack[-1].name if self._stack else None

        if self._profile:
            entry = TimingEntry(name=name, duration=0, start_time=start, end_time=start, parent=parent)
            self._stack.append(entry)

        if self._level >= LogLevel.VERBOSE:
            self.verbose_info(f"Starting {name}...")

        try:
            yield
        finally:
            end = time.time()
            duration = end - start

            if self._profile:
                entry = self._stack.pop()
                entry.duration = duration
                entry.end_time = end
                self._timings.append(entry)

            if self._level >= LogLevel.VERBOSE:
                self.verbose_info(f"Finished {name} after {duration:.1f}s")

    @contextmanager
    def step(self, index: int, total: int, name: str):
        """Context manager for a logical step in the startup process.

        Usage:
            with logger.step(1, 5, "Starting PostgreSQL"):
                start_postgresql()

        Args:
            index: Step number (1-based)
            total: Total number of steps
            name: Description of the step
        """
        if self._level >= LogLevel.VERBOSE:
            self.info(f"  {name}...")

        start = time.time()
        parent = self._stack[-1].name if self._stack else None

        if self._profile:
            entry = TimingEntry(
                name=f"Step {index}: {name}",
                duration=0,
                start_time=start,
                end_time=start,
                parent=parent
            )
            self._stack.append(entry)

        try:
            yield
        finally:
            end = time.time()
            duration = end - start

            if self._profile:
                entry = self._stack.pop()
                entry.duration = duration
                entry.end_time = end
                self._timings.append(entry)

            if self._level >= LogLevel.VERBOSE and not self._profile:
                # Only show completion in VERBOSE mode (DEBUG shows via timed)
                self.info(f"  {name} - done")

    @contextmanager
    def progress_context(self, name: str, total: int, report_interval: int = 5):
        """Context manager for tracking progress of a repetitive operation.

        Usage:
            with logger.progress_context("Waiting for service", 30) as progress:
                for i in range(30):
                    check_service()
                    progress.update(i + 1)

        Args:
            name: Name of the operation
            total: Total number of iterations
            report_interval: How often to report progress (every N iterations)

        Returns:
            ProgressContext object with update() method
        """
        state = ProgressState(
            total=total,
            current=0,
            start_time=time.time(),
            name=name
        )

        class ProgressContext:
            def __init__(self, logger_ref: Logger, state_ref: ProgressState, report_interval: int):
                self._logger = logger_ref
                self._state = state_ref
                self._report_interval = report_interval

            def update(self, current: int) -> None:
                """Update progress."""
                self._state.current = current
                if (current % self._report_interval == 0 or current == self._state.total):
                    elapsed = time.time() - self._state.start_time
                    self._logger.progress(
                        f"{self._state.name}",
                        current,
                        self._state.total
                    )

        if self._level >= LogLevel.VERBOSE:
            self.verbose_info(f"{name}...")

        try:
            yield ProgressContext(self, state, report_interval)
        finally:
            elapsed = time.time() - state.start_time
            if self._level >= LogLevel.VERBOSE:
                self.verbose_info(f"{name} ready after {elapsed:.1f}s ({state.total} attempts)")

    def print_summary(self) -> None:
        """Print timing summary if profiling is enabled."""
        if not self._profile or not self._timings:
            return

        total_duration = time.time() - self._start_time

        self._output.write("\n")
        self._output.write("=" * 40 + "\n")
        self._output.write("TIMING SUMMARY\n")
        self._output.write("=" * 40 + "\n")
        self._output.write(f"Total duration: {total_duration:.1f}s\n")
        self._output.write("\n")

        # Group and display steps
        step_entries = [t for t in self._timings if t.name.startswith("Step ") or t.parent is None]

        self._output.write("Breakdown:\n")
        for entry in step_entries:
            percentage = (entry.duration / total_duration * 100) if total_duration > 0 else 0
            self._output.write(f"  {entry.name.ljust(35)} {entry.duration:5.1f}s ({percentage:2.0f}%)\n")

        # Identify bottlenecks (top 2 by duration)
        self._output.write("\nBottlenecks identified:\n")
        sorted_by_duration = sorted(step_entries, key=lambda x: x.duration, reverse=True)
        for i, entry in enumerate(sorted_by_duration[:2]):
            percentage = (entry.duration / total_duration * 100) if total_duration > 0 else 0
            self._output.write(f"  {i + 1}. {entry.name}: {entry.duration:.1f}s ({percentage:.0f}% of total)\n")

        self._output.write("=" * 40 + "\n")
        self._output.flush()


# Default logger instance (can be replaced)
_default_logger: Logger | None = None


def get_default_logger() -> Logger:
    """Get the default logger instance."""
    global _default_logger
    if _default_logger is None:
        _default_logger = Logger()
    return _default_logger


def set_default_logger(logger: Logger) -> None:
    """Set the default logger instance."""
    global _default_logger
    _default_logger = logger
