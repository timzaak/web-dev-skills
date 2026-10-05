#!/usr/bin/env python3
"""Compute the next t-super-run-all pipeline action from persisted state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PHASE_ORDER = (
    "backend",
    "frontend",
    "extension",
    "miniapp",
    "flutter",
    "web-demo",
    "extension-demo",
    "flutter-demo",
)
CHAIN = ("review", "simplify", "push")
PHASE_STATUSES = ("pending", "in_progress", "failed", "blocked", "completed", "skipped")
STEP_STATUSES = ("pending", "in_progress", "failed", "blocked", "completed")


class PipelineError(Exception):
    pass


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PipelineError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PipelineError(f"{path} must contain a JSON object")
    return data


def validate_state(state: dict) -> list[str]:
    active = state.get("active_phases")
    if not isinstance(active, list) or not active:
        raise PipelineError("state.active_phases must be a non-empty list")
    unknown = [phase for phase in active if phase not in PHASE_ORDER]
    if unknown:
        raise PipelineError(f"unsupported phases in active_phases: {', '.join(unknown)}")
    phases = state.get("phases")
    if not isinstance(phases, dict):
        raise PipelineError("state.phases must be an object")
    for phase, entry in phases.items():
        if phase not in PHASE_ORDER:
            raise PipelineError(f"unsupported phase entry in state.phases: {phase}")
        status = entry.get("status") if isinstance(entry, dict) else None
        if status is not None and status not in PHASE_STATUSES:
            raise PipelineError(f"invalid status for phase {phase}: {status}")
    return [phase for phase in PHASE_ORDER if phase in set(active)]


def validate_cursor(cursor: dict) -> dict:
    chain = cursor.get("chain")
    if chain != list(CHAIN):
        raise PipelineError(f"pipeline chain must be {list(CHAIN)}, got: {chain}")
    phases = cursor.get("phases")
    if not isinstance(phases, dict):
        raise PipelineError("pipeline.phases must be an object")
    for phase, steps in phases.items():
        if not isinstance(steps, dict):
            raise PipelineError(f"pipeline.phases.{phase} must be an object")
        for step, entry in steps.items():
            if step not in CHAIN:
                raise PipelineError(f"unknown pipeline step for phase {phase}: {step}")
            status = entry.get("status") if isinstance(entry, dict) else None
            if status is None or status not in STEP_STATUSES:
                raise PipelineError(f"invalid status for pipeline step {phase}.{step}: {status}")
    return phases


def step_status(cursor_phases: dict, phase: str, step: str) -> str:
    entry = cursor_phases.get(phase, {}).get(step)
    return entry.get("status", "pending") if isinstance(entry, dict) else "pending"


def compute(feature: str, state: dict | None, cursor: dict | None) -> dict:
    cursor_phases = validate_cursor(cursor) if cursor is not None else {}

    if state is None:
        return {
            "status": "ok",
            "action": "plan_first_phase",
            "phase": None,
            "reason": "no super-run state; derive active_phases and plan the first phase",
            "ordered_active_phases": [],
            "phase_summary": {},
        }

    ordered = validate_state(state)
    result_phases: list[str] = []
    summary: dict[str, dict] = {}

    for phase in ordered:
        entry = state["phases"].get(phase)
        phase_status = entry.get("status") if isinstance(entry, dict) else None

        if phase_status is None or phase_status in ("pending", "in_progress", "failed"):
            summary[phase] = {"phase": phase_status or "pending", "chain": "pending"}
            result_phases.append(phase)
            return {
                "status": "ok",
                "action": "run_phase",
                "phase": phase,
                "reason": f"phase status: {phase_status or 'not planned'}",
                "ordered_active_phases": ordered,
                "phase_summary": summary,
            }
        if phase_status == "blocked":
            summary[phase] = {"phase": "blocked", "chain": "pending"}
            return {
                "status": "blocked",
                "action": "none",
                "phase": phase,
                "reason": f"phase {phase} is blocked; resolve the blocking condition before continuing",
                "ordered_active_phases": ordered,
                "phase_summary": summary,
            }
        if phase_status == "skipped":
            summary[phase] = {"phase": "skipped", "chain": "skipped"}
            continue

        for step in CHAIN:
            status = step_status(cursor_phases, phase, step)
            if status in ("pending", "in_progress", "failed"):
                summary[phase] = {"phase": "completed", "chain": status}
                return {
                    "status": "ok",
                    "action": step,
                    "phase": phase,
                    "reason": f"quality step {phase}.{step}: {status}",
                    "ordered_active_phases": ordered,
                    "phase_summary": summary,
                }
            if status == "blocked":
                summary[phase] = {"phase": "completed", "chain": "blocked"}
                return {
                    "status": "blocked",
                    "action": "none",
                    "phase": phase,
                    "reason": f"quality step {phase}.{step} is blocked",
                    "ordered_active_phases": ordered,
                    "phase_summary": summary,
                }
        summary[phase] = {"phase": "completed", "chain": "completed"}
        result_phases.append(phase)

    return {
        "status": "done",
        "action": "none",
        "phase": None,
        "reason": "all active phases and quality chains are complete",
        "ordered_active_phases": ordered,
        "phase_summary": summary,
    }


def describe(result: dict) -> str:
    if result["action"] == "none":
        return f"{result['status']}: {result['reason']}"
    target = f" for phase {result['phase']}" if result["phase"] else ""
    return f"{result['status']}: {result['action']}{target} ({result['reason']})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute the next t-super-run-all pipeline action from persisted state."
    )
    parser.add_argument("feature")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    feature = args.feature.strip()
    if not feature or "/" in feature or "\\" in feature or feature in (".", ".."):
        result = {
            "status": "error",
            "action": "none",
            "phase": None,
            "reason": f"invalid feature name: {args.feature!r}",
            "ordered_active_phases": [],
            "phase_summary": {},
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["reason"])
        return 1

    run_dir = args.root.resolve() / ".ai" / "super-run" / feature
    try:
        state = load_json(run_dir / ".state.json")
        cursor = load_json(run_dir / ".pipeline.json")
        result = compute(feature, state, cursor)
        exit_code = 0 if result["status"] in ("ok", "done", "blocked") else 1
    except PipelineError as exc:
        result = {
            "status": "error",
            "action": "none",
            "phase": None,
            "reason": str(exc),
            "ordered_active_phases": [],
            "phase_summary": {},
        }
        exit_code = 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(describe(result))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
