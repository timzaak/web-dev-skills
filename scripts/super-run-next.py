#!/usr/bin/env python3
"""Compute the next t-super-run-all pipeline action from persisted state."""

from __future__ import annotations

import argparse
import hashlib
import json
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
    if not path.exists():
        return None
    if not path.is_file():
        raise PipelineError(f"{path} must be a JSON file")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PipelineError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PipelineError(f"{path} must contain a JSON object")
    return data


def validate_identity(data: dict, feature: str, label: str) -> None:
    if data.get("feature") != feature:
        raise PipelineError(f"{label}.feature must match {feature!r}")


def validate_counter(entry: dict, label: str) -> None:
    count = entry.get("failures_without_progress", 0)
    if type(count) is not int or count < 0:
        raise PipelineError(f"{label}.failures_without_progress must be a non-negative integer")


def aggregate(tasks: dict) -> str:
    statuses = [task["status"] for task in tasks.values()]
    for status in ("blocked", "failed", "in_progress", "pending"):
        if status in statuses:
            return status
    return "skipped" if all(status == "skipped" for status in statuses) else "completed"


def validate_state(state: dict, feature: str) -> list[str]:
    validate_identity(state, feature, "state")
    active = state.get("active_phases")
    if not isinstance(active, list) or not active:
        raise PipelineError("state.active_phases must be a non-empty list")
    if any(not isinstance(phase, str) for phase in active):
        raise PipelineError("state.active_phases entries must be strings")
    if len(set(active)) != len(active):
        raise PipelineError("state.active_phases must not contain duplicates")
    unknown = [phase for phase in active if phase not in PHASE_ORDER]
    if unknown:
        raise PipelineError(f"unsupported phases in active_phases: {', '.join(unknown)}")
    phases = state.get("phases")
    if not isinstance(phases, dict):
        raise PipelineError("state.phases must be an object")
    for phase, entry in phases.items():
        if phase not in active:
            raise PipelineError(f"inactive phase entry in state.phases: {phase}")
        status = entry.get("status") if isinstance(entry, dict) else None
        if status not in PHASE_STATUSES:
            raise PipelineError(f"invalid status for phase {phase}: {status}")
        if not isinstance(entry.get("plan"), str) or not entry["plan"]:
            raise PipelineError(f"state.phases.{phase}.plan must be a non-empty string")
        revision = entry.get("validation_revision", 0)
        if type(revision) is not int or revision < 0:
            raise PipelineError(f"state.phases.{phase}.validation_revision must be a non-negative integer")
        tasks = entry.get("tasks")
        allowed = {"dev", "accept"} if phase.endswith("demo") else {"dev", "test", "accept"}
        if not isinstance(tasks, dict) or not {"dev", "accept"} <= tasks.keys() or not tasks.keys() <= allowed:
            raise PipelineError(f"invalid tasks for phase {phase}; dev and accept are required")
        for name, task in tasks.items():
            label = f"state.phases.{phase}.tasks.{name}"
            if not isinstance(task, dict) or task.get("status") not in PHASE_STATUSES:
                raise PipelineError(f"invalid status for {label}")
            if not isinstance(task.get("agent_spec"), str) or not task["agent_spec"]:
                raise PipelineError(f"{label}.agent_spec must be a non-empty string")
            for field in ("references", "evidence"):
                value = task.get(field)
                if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
                    raise PipelineError(f"{label}.{field} must be a list of non-empty strings")
            validate_counter(task, label)
            if task["status"] in ("completed", "skipped") and not task["evidence"]:
                raise PipelineError(f"{label} requires completion or inapplicability evidence")
        if tasks["accept"]["status"] == "skipped" and any(task["status"] != "skipped" for task in tasks.values()):
            raise PipelineError(f"phase {phase} cannot skip accept alone")
        if status != aggregate(tasks):
            raise PipelineError(f"phase {phase} status disagrees with its tasks")
    current = state.get("current_phase")
    if "current_phase" not in state or (current is not None and (not isinstance(current, str) or current not in phases)):
        raise PipelineError("state.current_phase must be null or a planned active phase")
    sources = state.get("sources")
    design = sources.get("design") if isinstance(sources, dict) else None
    if not isinstance(design, dict) or not isinstance(design.get("fingerprint"), str) or not design["fingerprint"]:
        raise PipelineError("state.sources.design.fingerprint must be a non-empty string")
    if not isinstance(design.get("main"), str) or not design["main"]:
        raise PipelineError("state.sources.design.main must be a non-empty string")
    documents = design.get("documents")
    if not isinstance(documents, list) or not documents or any(not isinstance(item, str) or not item for item in documents):
        raise PipelineError("state.sources.design.documents must be a non-empty string list")
    for field in ("requirements", "decisions", "research"):
        if not isinstance(sources.get(field), list):
            raise PipelineError(f"state.sources.{field} must be a list")
    return [phase for phase in PHASE_ORDER if phase in set(active)]


def validate_cursor(cursor: dict, feature: str) -> dict:
    validate_identity(cursor, feature, "pipeline")
    chain = cursor.get("chain")
    if chain != list(CHAIN):
        raise PipelineError(f"pipeline chain must be {list(CHAIN)}, got: {chain}")
    phases = cursor.get("phases")
    if not isinstance(phases, dict):
        raise PipelineError("pipeline.phases must be an object")
    for phase, steps in phases.items():
        if phase not in PHASE_ORDER:
            raise PipelineError(f"unsupported pipeline phase: {phase}")
        if not isinstance(steps, dict):
            raise PipelineError(f"pipeline.phases.{phase} must be an object")
        for step, entry in steps.items():
            if step == "input_fingerprint":
                if not isinstance(entry, str) or not entry.startswith("sha256:") or len(entry) != 71 or any(char not in "0123456789abcdef" for char in entry[7:]):
                    raise PipelineError(f"invalid input_fingerprint for phase {phase}")
                continue
            if step not in CHAIN:
                raise PipelineError(f"unknown pipeline step for phase {phase}: {step}")
            status = entry.get("status") if isinstance(entry, dict) else None
            if status is None or status not in STEP_STATUSES:
                raise PipelineError(f"invalid status for pipeline step {phase}.{step}: {status}")
            validate_counter(entry, f"pipeline.phases.{phase}.{step}")
            if step == "push":
                session = entry.get("ci_session")
                if session is not None and (not isinstance(session, str) or not session or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in session)):
                    raise PipelineError(f"invalid ci_session for phase {phase}")
                fingerprint = entry.get("accepted_worktree_fingerprint")
                if fingerprint is not None and (not isinstance(fingerprint, str) or not fingerprint.startswith("sha256:") or len(fingerprint) != 71 or any(char not in "0123456789abcdef" for char in fingerprint[7:])):
                    raise PipelineError(f"invalid accepted_worktree_fingerprint for phase {phase}")
    return phases


def step_status(cursor_phases: dict, phase: str, step: str) -> str:
    entry = cursor_phases.get(phase, {}).get(step)
    return entry.get("status", "pending") if isinstance(entry, dict) else "pending"


def input_fingerprint(state: dict, phase: str) -> str:
    payload = {"sources": state["sources"], "phase": state["phases"][phase]}
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute(feature: str, state: dict | None, cursor: dict | None) -> dict:
    cursor_phases = validate_cursor(cursor, feature) if cursor is not None else {}

    if state is None:
        if cursor is not None:
            raise PipelineError("pipeline cursor exists without super-run state; preserve it and resolve the missing state")
        return {
            "status": "ok",
            "action": "plan_first_phase",
            "phase": None,
            "reason": "no super-run state; derive active_phases and plan the first phase",
            "ordered_active_phases": [],
            "phase_summary": {},
        }

    ordered = validate_state(state, feature)
    if any(phase not in ordered for phase in cursor_phases):
        raise PipelineError("pipeline contains phases outside state.active_phases")
    summary: dict[str, dict] = {}

    for phase in ordered:
        entry = state["phases"].get(phase)
        phase_status = entry.get("status") if isinstance(entry, dict) else None

        if phase_status is None or phase_status in ("pending", "in_progress", "failed"):
            summary[phase] = {"phase": phase_status or "pending", "chain": "pending"}
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
                "status": "ok",
                "action": "check_blocked",
                "phase": phase,
                "reason": f"check whether the blocking condition for phase {phase} has been resolved",
                "step": None,
                "ordered_active_phases": ordered,
                "phase_summary": summary,
            }
        if phase_status == "skipped":
            summary[phase] = {"phase": "skipped", "chain": "skipped"}
            continue

        fingerprint = input_fingerprint(state, phase)
        bound = cursor_phases.get(phase, {}).get("input_fingerprint")
        if phase in cursor_phases and bound != fingerprint:
            return {
                "status": "ok", "action": "reset_quality", "phase": phase,
                "reason": "quality chain is unbound or its accepted input changed",
                "input_fingerprint": fingerprint,
                "ordered_active_phases": ordered, "phase_summary": summary,
            }

        for step in CHAIN:
            status = step_status(cursor_phases, phase, step)
            if status in ("pending", "in_progress", "failed"):
                summary[phase] = {"phase": "completed", "chain": status}
                return {
                    "status": "ok",
                    "action": step,
                    "phase": phase,
                    "reason": f"quality step {phase}.{step}: {status}",
                    "input_fingerprint": fingerprint,
                    "ordered_active_phases": ordered,
                    "phase_summary": summary,
                }
            if status == "blocked":
                summary[phase] = {"phase": "completed", "chain": "blocked"}
                return {
                    "status": "ok",
                    "action": "check_blocked",
                    "phase": phase,
                    "reason": f"check whether the blocking condition for {phase}.{step} has been resolved",
                    "step": step,
                    "input_fingerprint": fingerprint,
                    "ordered_active_phases": ordered,
                    "phase_summary": summary,
                }
        summary[phase] = {"phase": "completed", "chain": "completed"}

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
    if not feature or any(char in '/\\:<>"|?*' or ord(char) < 32 for char in feature) or feature in (".", ".."):
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
