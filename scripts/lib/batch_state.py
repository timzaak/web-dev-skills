"""Resumable batch state shared by the Demo run-all helpers.

A batch is one JSON file under `.ai/quality/`. It lists the discovered files, the
results recorded so far and a cursor naming the file in flight. The skill that
drives the loop advances a batch only through `start_file`, `record_result` and
`complete`, so the web and the Flutter helper persist the same layout.
"""

import json
from datetime import datetime
from pathlib import Path

from .paths import REPO_ROOT

QUALITY_DIR = REPO_ROOT / ".ai" / "quality"


class BatchError(ValueError):
    """The batch file is missing or unreadable, or the request does not fit its state."""


def ensure_quality_dir() -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)


def display_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def resolve_report_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def load_report(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BatchError(str(exc)) from exc
    if not isinstance(payload, dict):
        raise BatchError(f"Batch report is not a JSON object: {path}")
    return payload


def save_report(path: Path, payload: dict[str, object]) -> None:
    """Write through a temp file (an interrupted write never truncates the batch) and stamp `updated_at`."""
    payload["updated_at"] = display_now()
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def _reports_newest_first(report_prefix: str) -> list[Path]:
    return sorted(
        QUALITY_DIR.glob(f"{report_prefix}-*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def latest_report(report_prefix: str) -> Path | None:
    """The most recently written batch file for `report_prefix`, whatever its status."""
    candidates = _reports_newest_first(report_prefix)
    return candidates[0] if candidates else None


def latest_running_report(report_prefix: str) -> Path | None:
    """The most recently written batch that is still `running`; unreadable files are skipped."""
    for path in _reports_newest_first(report_prefix):
        try:
            if json.loads(path.read_text(encoding="utf-8")).get("batch_status") == "running":
                return path
        except (OSError, json.JSONDecodeError):
            continue
    return None


def discovered_files(payload: dict[str, object]) -> list[str]:
    files = payload.get("discovered_files")
    if not isinstance(files, list) or not files:
        raise BatchError("Latest batch report does not contain discovered_files")
    normalized = [str(item) for item in files]
    if any(not item for item in normalized):
        raise BatchError("Latest batch report contains an invalid discovered_files entry")
    return normalized


def recorded_entries(payload: dict[str, object]) -> list[dict[str, object]]:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise BatchError("Batch report does not contain entries")
    return entries


def start_file(payload: dict[str, object], index: int) -> None:
    """Point the cursor at `discovered_files[index]`, which must be the next unfinished file."""
    files = discovered_files(payload)
    entries = recorded_entries(payload)
    if payload.get("batch_status") != "running":
        raise BatchError("Batch is not running")
    if index != len(entries):
        raise BatchError("Checkpoint index must equal the completed entry count")
    if index < 0 or index >= len(files):
        raise BatchError("Checkpoint index is out of range")
    payload["current_index"] = index
    payload["current_file"] = files[index]
    payload.pop("last_error", None)


def record_result(
    payload: dict[str, object],
    *,
    status: str,
    exit_code: int,
    duration: float,
    run_id: str,
    logs: str,
    error: str = "",
    fixed: bool = False,
) -> None:
    """Append the result of the file under the cursor, then clear the cursor."""
    files = discovered_files(payload)
    entries = recorded_entries(payload)
    if payload.get("batch_status") != "running":
        raise BatchError("Batch is not running")
    index = len(entries)
    if index >= len(files):
        raise BatchError("Batch already contains all file results")
    if payload.get("current_file") != files[index]:
        raise BatchError("Current file does not match the next unfinished file")
    if fixed and status != "passed":
        raise BatchError("Only a passed result can be marked fixed")
    entries.append({
        "test_file": files[index],
        "status": status,
        "exit_code": exit_code,
        "duration": duration,
        "run_id": run_id,
        "logs": logs,
        "error": error if status == "failed" else "",
        "fixed": fixed,
    })
    payload["current_index"] = index + 1
    payload["current_file"] = ""
    payload.pop("last_error", None)


def tally(entries: list[dict[str, object]]) -> tuple[int, int]:
    """`(passed, failed)`: every entry that is not `passed` counts as failed."""
    passed = sum(1 for entry in entries if isinstance(entry, dict) and entry.get("status") == "passed")
    return passed, len(entries) - passed


def total_duration(entries: list[dict[str, object]]) -> float:
    return round(sum(
        float(entry.get("duration", 0.0) or 0.0)
        for entry in entries
        if isinstance(entry, dict)
    ), 3)


def complete(payload: dict[str, object]) -> None:
    """Mark the batch completed once every discovered file has a recorded result."""
    files = discovered_files(payload)
    entries = recorded_entries(payload)
    if len(entries) != len(files):
        raise BatchError(f"batch is incomplete: expected {len(files)} entries, found {len(entries)}")
    payload["batch_status"] = "completed"
    payload["current_index"] = len(entries)
    payload["current_file"] = ""
    payload["passed_files"], payload["failed_files"] = tally(entries)
