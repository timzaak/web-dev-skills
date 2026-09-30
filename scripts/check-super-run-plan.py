#!/usr/bin/env python3
"""Audit super-run artifacts and atomically checkpoint controller-owned state.

Semantic coverage and evidence validity remain the controller/accept's job.
The schema and transition rules live in protocols/super-run-state-contract.md.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("super_run_design", PLUGIN / "scripts/check-design.py")
assert SPEC and SPEC.loader
design = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = design
SPEC.loader.exec_module(design)

PHASES = {"backend", "frontend", "extension", "miniapp", "flutter",
          "web-demo", "extension-demo", "flutter-demo"}
SLOTS = ("dev", "test", "accept")
STATUSES = {"pending", "in_progress", "failed", "blocked", "completed", "skipped"}
TERMINAL = {"completed", "skipped"}
TRANSITIONS = {
    "pending": {"in_progress", "blocked", "skipped"},
    "in_progress": {"completed", "failed", "blocked", "pending"},
    "failed": {"in_progress", "blocked", "pending"},
    "blocked": {"pending"},
    "completed": {"pending"},
    "skipped": {"pending"},
}


class Invalid(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise Invalid(code, message)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Invalid("JSON_INVALID", f"{path}: {exc}") from exc


def object_value(value, location: str) -> dict:
    require(isinstance(value, dict), "SCHEMA_INVALID", f"{location}: expected object")
    return value


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def integer(value, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def project_path(root: Path, value: str, boundary: Path | None = None) -> Path:
    require(nonempty(value), "PATH_INVALID", repr(value))
    relative = Path(value)
    require(not relative.is_absolute() and not relative.drive, "PATH_INVALID", value)
    result = (root / relative).resolve()
    require(result.is_relative_to((boundary or root).resolve()), "PATH_OUTSIDE_SCOPE", value)
    return result


def text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise Invalid("ARTIFACT_MISSING", f"{path}: {exc}") from exc


def aggregate(statuses) -> str:
    statuses = list(statuses)
    require(bool(statuses) and all(s in STATUSES for s in statuses),
            "STATUS_INVALID", str(statuses))
    for status in ("blocked", "failed", "in_progress", "pending"):
        if status in statuses:
            return status
    return "skipped" if all(s == "skipped" for s in statuses) else "completed"


def inventory(main: Path) -> list[dict]:
    content = text_file(main)
    rows = []
    for kind, heading in (("coverage", "2.5 设计覆盖矩阵"),
                          ("operation", "4.3 跨端契约"), ("impact", "8. 文件影响范围")):
        for row in design.table_rows(content, heading):
            normalized = [design.clean_cell(cell) for cell in row]
            digest = hashlib.sha256(json.dumps(normalized, ensure_ascii=False).encode()).hexdigest()[:16]
            rows.append({"source_id": f"{kind}:{digest}", "kind": kind, "content": normalized})
    require(any(row["kind"] == "coverage" for row in rows), "COVERAGE_EMPTY", str(main))
    require(len({row["source_id"] for row in rows}) == len(rows),
            "SOURCE_DUPLICATE", "Design contains duplicate source rows")
    return rows


def state_items(phase: dict) -> dict:
    return {item_id: item for slot in phase["slots"].values()
            for item_id, item in slot["items"].items()}


def shape(state: dict, feature: str) -> None:
    object_value(state, "state")
    require(state.get("schema_version") == 2, "SCHEMA_VERSION",
            "Expected schema_version=2; preserve legacy state and rebuild explicitly")
    require(state.get("feature") == feature, "FEATURE_MISMATCH", feature)
    require(integer(state.get("sequence"), 1), "SEQUENCE_INVALID", "sequence must be positive")
    active = state.get("active_phases")
    require(isinstance(active, list) and bool(active) and all(isinstance(p, str) and p in PHASES for p in active)
            and len(set(active)) == len(active), "PHASE_INVALID", "active_phases")
    phases = object_value(state.get("phases"), "phases")
    require(bool(phases) and set(phases) <= set(active), "PHASE_INVALID", "planned phases")
    require(state.get("current_phase") is None or isinstance(state["current_phase"], str) and state["current_phase"] in phases,
            "PHASE_INVALID", "current_phase")
    running = 0
    for name, phase in phases.items():
        object_value(phase, name)
        require(integer(phase.get("revision"), 1), "REVISION_INVALID", name)
        require(nonempty(phase.get("index")) and nonempty(phase.get("design_fingerprint")),
                "SCHEMA_INVALID", f"{name}: index/design_fingerprint")
        slots = object_value(phase.get("slots"), f"{name}.slots")
        require({"dev", "accept"} <= set(slots) <= set(SLOTS), "SLOT_INVALID", name)
        require(not name.endswith("-demo") or "test" not in slots, "SLOT_INVALID", name)
        ids = set()
        for slot_name, slot in slots.items():
            object_value(slot, f"{name}/{slot_name}")
            require(nonempty(slot.get("manifest")), "SCHEMA_INVALID", "manifest")
            items = object_value(slot.get("items"), f"{name}/{slot_name}/items")
            require(bool(items), "ITEMS_EMPTY", f"{name}/{slot_name}")
            for item_id, item in items.items():
                require(bool(re.fullmatch(r"[A-Z][A-Z0-9]*-[A-Z][0-9]+", item_id)),
                        "ITEM_ID_INVALID", item_id)
                require(item_id not in ids, "ITEM_DUPLICATE", item_id)
                ids.add(item_id)
                object_value(item, item_id)
                require(isinstance(item.get("status"), str) and item["status"] in STATUSES, "STATUS_INVALID", item_id)
                require(nonempty(item.get("file")) and nonempty(item.get("agent")),
                        "SCHEMA_INVALID", f"{item_id}: file/agent")
                require(integer(item.get("attempt")) and integer(item.get("failures_without_progress")),
                        "SCHEMA_INVALID", f"{item_id}: counters")
                require(isinstance(item.get("evidence"), list) and all(nonempty(p) for p in item["evidence"]),
                        "SCHEMA_INVALID", f"{item_id}: evidence")
                if item["status"] in {"in_progress", "completed", "failed"}:
                    require(item["attempt"] > 0, "ATTEMPT_INVALID", item_id)
                if item["status"] in {"failed", "blocked"}:
                    require(nonempty(item.get("last_error")), "ERROR_MISSING", item_id)
                if item["status"] == "skipped":
                    require(nonempty(item.get("reason")), "REASON_MISSING", item_id)
                running += item["status"] == "in_progress"
            require(slot.get("status") == aggregate(i["status"] for i in items.values()),
                    "AGGREGATION_INVALID", f"{name}/{slot_name}")
        require(phase.get("status") == aggregate(s["status"] for s in slots.values()),
                "AGGREGATION_INVALID", name)
        if phase["status"] == "completed":
            require(slots["accept"]["status"] == "completed", "ACCEPTANCE_MISSING", name)
        if state.get("current_phase") == name:
            require(phase["status"] not in TERMINAL, "PHASE_INVALID", "terminal current_phase")
    require(running <= 1, "CONCURRENT_WORKERS", "Only one item may be in_progress")


def metadata(content: str, key: str) -> str | None:
    header = content.split("## Goal", 1)[0]
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", header, re.MULTILINE)
    return match.group(1).strip().strip("\"'") if match else None


def validate_plan(state: dict, root: Path, feature: str, phase_name: str, evidence: bool,
                  check_sources: bool = True) -> list[str]:
    shape(state, feature)
    require(phase_name in state["phases"], "PHASE_UNPLANNED", phase_name)
    phase = state["phases"][phase_name]
    base = root / ".ai/super-run" / feature / phase_name / f"r{phase['revision']}"
    require(project_path(root, phase["index"], base) == (base / "index.md").resolve(),
            "INDEX_INVALID", phase["index"])
    index = text_file(base / "index.md")
    require(bool(index.strip()), "INDEX_INVALID", "empty index")
    main = root / ".ai/design" / f"{feature}.md"
    if check_sources:
        design_state = object_value(read_json(main.with_suffix("") / ".state.json"), "design state")
        require(design_state.get("status") == "complete", "DESIGN_INCOMPLETE", str(main))
        require(phase["design_fingerprint"] == design.design_fingerprint(main), "FINGERPRINT_MISMATCH", phase_name)
    order = []
    files = set()
    test_types = []
    for slot_name in SLOTS:
        if slot_name not in phase["slots"]:
            continue
        slot = phase["slots"][slot_name]
        manifest = project_path(root, slot["manifest"], base)
        require(manifest == (base / f"{slot_name}.md").resolve(), "MANIFEST_INVALID", str(manifest))
        rows = design.table_rows(text_file(manifest), "## Items")
        require(all(len(row) == 4 for row in rows), "MANIFEST_INVALID", str(manifest))
        manifest_ids = [design.clean_cell(row[0]) for row in rows]
        require(len(manifest_ids) == len(set(manifest_ids)) and set(manifest_ids) == set(slot["items"]),
                "MANIFEST_ITEMS_MISMATCH", str(manifest))
        for row in rows:
            item_id, title, agent, file = [design.clean_cell(cell) for cell in row]
            item = slot["items"][item_id]
            require(agent == item["agent"] and file == item["file"], "MANIFEST_ITEM_MISMATCH", item_id)
            item_path = project_path(root, file, base / slot_name)
            require(item_path.parent == (base / slot_name).resolve() and item_path.suffix == ".md",
                    "ITEM_PATH_INVALID", file)
            require(item_path not in files, "ITEM_FILE_DUPLICATE", file)
            files.add(item_path)
            content = text_file(item_path)
            for key, value in (("id", item_id), ("title", title), ("agent", agent)):
                require(metadata(content, key) == value, "ITEM_METADATA_MISMATCH", f"{item_id}: {key}")
            headings = re.findall(r"^## (.+)\s*$", content, re.MULTILINE)
            require(headings == ["Goal", "Work", "Files", "Validation", "Handoff"],
                    "ITEM_SECTIONS_INVALID", item_id)
            for heading in headings[:-1]:
                require(len(design.section(content, f"## {heading}").splitlines()) > 1,
                        "ITEM_SECTION_EMPTY", f"{item_id}: {heading}")
            expected_agent = f"{phase_name}-{slot_name}"
            if slot_name == "dev" and item.get("repair_for"):
                repair_evidence = item.get("repair_evidence")
                require(isinstance(item["repair_for"], str) and item["repair_for"] in state_items(phase)
                        and item["repair_for"] != item_id and nonempty(item.get("reason"))
                        and isinstance(repair_evidence, list) and bool(repair_evidence)
                        and all(nonempty(path) for path in repair_evidence),
                        "REPAIR_INVALID", item_id)
                for path in repair_evidence:
                    require(project_path(root, path.split("#", 1)[0]).is_file(), "REPAIR_EVIDENCE_MISSING", path)
                require(agent in {f"{p}-dev" for p in PHASES}, "AGENT_MISMATCH", item_id)
                expected_agent = agent
            if phase_name == "backend" and slot_name == "test":
                kind = metadata(content, "test_item_type")
                require(kind in {"authoring", "runner"}, "TEST_ITEM_TYPE_INVALID", item_id)
                test_types.append(kind)
                expected_agent = "general-purpose" if kind == "runner" else "backend-test"
                if kind == "runner":
                    require("protocols/backend-test-execution.md" in content
                            and "### Expected Test Manifest" in content,
                            "RUNNER_CONTRACT_MISSING", item_id)
            require(agent == expected_agent, "AGENT_MISMATCH", item_id)
            require(agent == "general-purpose" or (PLUGIN / "agents" / f"{agent}.md").is_file(),
                    "AGENT_MISSING", agent)
            if evidence and item["status"] == "completed":
                require(bool(item["evidence"]), "EVIDENCE_MISSING", item_id)
                for path in item["evidence"]:
                    require(project_path(root, path.split("#", 1)[0]).is_file(), "EVIDENCE_MISSING", path)
                if slot_name == "accept":
                    require(item.get("acceptance_result") in {"ACCEPTED", "ACCEPTED_WITH_IMPROVEMENTS"}
                            and type(item.get("blocking_findings")) is int and item["blocking_findings"] == 0,
                            "ACCEPTANCE_INVALID", item_id)
                    report = item.get("report_path")
                    require(report in item["evidence"], "ACCEPTANCE_REPORT_MISSING", item_id)
            order.append(item_id)
    require(set(base.glob("*/*.md")) == files, "ORPHAN_ITEM", str(base))
    if test_types:
        require("runner" in test_types and test_types[-1] == "runner",
                "RUNNER_MISSING", phase_name)
    coverage = read_json(base / "coverage.json")
    require(isinstance(coverage, list), "COVERAGE_INVALID", str(base))
    expected_sources = {row["source_id"] for row in inventory(main)} if check_sources else None
    seen = set()
    for row in coverage:
        object_value(row, "coverage row")
        source = row.get("source_id")
        require(isinstance(source, str) and (expected_sources is None or source in expected_sources) and source not in seen,
                "COVERAGE_SOURCE_INVALID", str(source))
        seen.add(source)
        disposition = row.get("disposition")
        require(isinstance(disposition, str) and disposition in {"implement", "consume", "other_phase", "not_applicable"}
                and nonempty(row.get("reason")), "COVERAGE_INVALID", source)
        linked = row.get("items")
        require(isinstance(linked, list) and all(isinstance(i, str) and i in order for i in linked),
                "COVERAGE_ITEM_INVALID", source)
        if disposition in {"implement", "consume"}:
            require(bool(linked), "COVERAGE_ITEM_MISSING", source)
        else:
            require(not linked, "COVERAGE_INVALID", source)
        if disposition == "other_phase":
            require(row.get("phase") in state["active_phases"] and row["phase"] != phase_name,
                    "COVERAGE_PHASE_INVALID", source)
    if expected_sources is not None:
        require(seen == expected_sources, "COVERAGE_INCOMPLETE", str(sorted(expected_sources - seen)))
    return order


def plan_fingerprint(root: Path, phase: dict) -> str:
    digest = hashlib.sha256()
    paths = [Path(phase["index"]).with_name("coverage.json").as_posix()]
    for slot in phase["slots"].values():
        paths.append(slot["manifest"])
        paths.extend(item["file"] for item in slot["items"].values())
    for path in sorted(paths):
        content = text_file(project_path(root, path))
        # Execution evidence may be appended without changing the executable plan.
        content = re.split(r"(?m)^## Handoff\s*$", content, maxsplit=1)[0]
        digest.update(path.encode("utf-8") + b"\0" + content.encode("utf-8") + b"\0")
    return "sha256:" + digest.hexdigest()


def transitions(old: dict | None, new: dict, phase_name: str, order: list[str]) -> None:
    phase = new["phases"][phase_name]
    before = old["phases"].get(phase_name) if old else None
    if old:
        require(set(old["phases"]) <= set(new["phases"]), "PHASE_REMOVED", phase_name)
        for name, previous in old["phases"].items():
            if name == phase_name:
                continue
            current = new["phases"][name]
            if current != previous:
                # Other phases may only have completed evidence invalidated, never run/replan.
                allowed = json.loads(json.dumps(previous))
                for slot_name, slot in allowed["slots"].items():
                    for item_id, item in slot["items"].items():
                        updated = current.get("slots", {}).get(slot_name, {}).get("items", {}).get(item_id)
                        require(isinstance(updated, dict), "OTHER_PHASE_CHANGED", name)
                        if updated != item:
                            require(item["status"] in TERMINAL and updated["status"] == "pending"
                                    and nonempty(updated.get("reason")), "OTHER_PHASE_CHANGED", name)
                            item["status"] = "pending"
                            item["reason"] = updated["reason"]
                    slot["status"] = aggregate(i["status"] for i in slot["items"].values())
                allowed["status"] = aggregate(s["status"] for s in allowed["slots"].values())
                require(current == allowed, "OTHER_PHASE_CHANGED", name)
        require(set(new["phases"]) - set(old["phases"]) <= {phase_name},
                "OTHER_PHASE_PLANNED", phase_name)
    require(new["current_phase"] == (None if phase["status"] in TERMINAL else phase_name),
            "PHASE_INVALID", "checkpoint must point to requested phase or null")
    previous_items = state_items(before) if before else {}
    current_items = state_items(phase)
    replan = before is not None and phase["revision"] != before["revision"]
    if replan:
        require(phase["revision"] == before["revision"] + 1 and nonempty(phase.get("replan_reason")),
                "REVISION_INVALID", phase_name)
        require(all(item["status"] != "in_progress" for item in previous_items.values()),
                "REPLAN_WHILE_RUNNING", phase_name)
        removed = set(previous_items) - set(current_items)
        require(not removed or isinstance(phase.get("retired_items"), dict)
                and all(nonempty(phase["retired_items"].get(i)) for i in removed),
                "RETIRED_ITEM_UNEXPLAINED", str(sorted(removed)))
        require(all(i["status"] != "in_progress" for i in current_items.values()),
                "REPLAN_WHILE_RUNNING", "Activate a plan before dispatching")
    elif before:
        require(set(previous_items) == set(current_items)
                and before["index"] == phase["index"]
                and before["design_fingerprint"] == phase["design_fingerprint"],
                "PLAN_CHANGED_WITHOUT_REVISION", phase_name)
        for slot_name in set(before["slots"]) | set(phase["slots"]):
            require(slot_name in before["slots"] and slot_name in phase["slots"]
                    and before["slots"][slot_name]["manifest"] == phase["slots"][slot_name]["manifest"]
                    and set(before["slots"][slot_name]["items"]) == set(phase["slots"][slot_name]["items"]),
                    "PLAN_CHANGED_WITHOUT_REVISION", slot_name)
    for item_id, item in current_items.items():
        previous = previous_items.get(item_id)
        if previous is None:
            require(item["status"] in {"pending", "skipped"} and item["attempt"] == 0,
                    "NEW_ITEM_ALREADY_EXECUTED", item_id)
            continue
        if not replan:
            require(item["file"] == previous["file"] and item["agent"] == previous["agent"],
                    "PLAN_CHANGED_WITHOUT_REVISION", item_id)
        start, end = previous["status"], item["status"]
        require(start == end or end in TRANSITIONS[start], "TRANSITION_INVALID", f"{item_id}: {start} -> {end}")
        if end == "pending" and start != end:
            require(nonempty(item.get("reason")), "REASON_MISSING", item_id)
        dispatching = end == "in_progress" and start != end
        require(item["attempt"] == previous["attempt"] + int(dispatching), "ATTEMPT_INVALID", item_id)
        if dispatching:
            predecessors = order[:order.index(item_id)]
            require(all(current_items[i]["status"] in TERMINAL for i in predecessors),
                    "PREDECESSOR_UNFINISHED", item_id)
            require(item["failures_without_progress"] < 3, "RETRY_LIMIT", item_id)
        if item["failures_without_progress"] < previous["failures_without_progress"]:
            require(nonempty(item.get("progress_evidence")), "RETRY_RESET_UNEXPLAINED", item_id)


def run(args) -> dict:
    state_path = args.state.resolve()
    root = args.project_root.resolve() if args.project_root else state_path.parents[3]
    feature = state_path.parent.name
    require(state_path.parent == (root / ".ai/super-run" / feature).resolve()
            and state_path.name in {".state.json", ".state.next.json"},
            "STATE_PATH_INVALID", str(state_path))
    if args.inventory:
        require(not args.commit, "ARGUMENT_INVALID", "inventory is read-only")
        return {"status": "passed", "sources": inventory(root / ".ai/design" / f"{feature}.md")}
    candidate = read_json(state_path)
    if not args.commit:
        order = validate_plan(candidate, root, feature, args.phase, args.evidence)
        recorded = candidate["phases"][args.phase].get("plan_fingerprint")
        require(recorded is None or recorded == plan_fingerprint(root, candidate["phases"][args.phase]),
                "PLAN_CONTENT_CHANGED", args.phase)
        return {"status": "passed", "next_item": next((i for i in order
                if state_items(candidate["phases"][args.phase])[i]["status"] not in TERMINAL), None)}
    require(state_path.name == ".state.next.json" and integer(args.expected_sequence),
            "ARGUMENT_INVALID", "commit needs .state.next.json and --expected-sequence")
    target = state_path.with_name(".state.json")
    lock = state_path.with_name(".state.lock")
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise Invalid("STATE_LOCKED", str(lock)) from exc
    temporary = None
    try:
        with handle:
            handle.write(f"pid={os.getpid()}\n")
        old = read_json(target) if target.exists() else None
        if old is not None:
            shape(old, feature)
        sequence = old["sequence"] if old else 0
        require(sequence == args.expected_sequence and candidate["sequence"] == sequence + 1,
                "SEQUENCE_CONFLICT", f"expected={args.expected_sequence}, actual={sequence}")
        shape(candidate, feature)
        require(args.phase in candidate["phases"], "PHASE_UNPLANNED", args.phase)
        phase = candidate["phases"][args.phase]
        previous = old["phases"].get(args.phase) if old else None
        before_items = state_items(previous) if previous else {}
        check_sources = previous is None or phase["revision"] != previous["revision"] or any(
            item["status"] in {"in_progress", "completed"}
            and item["status"] != before_items.get(item_id, {}).get("status")
            for item_id, item in state_items(phase).items())
        # Re-read artifacts under the write lock; never promote a stale validation result.
        order = validate_plan(candidate, root, feature, args.phase, True, check_sources)
        fingerprint = plan_fingerprint(root, phase)
        if previous and phase["revision"] == previous["revision"]:
            require(previous.get("plan_fingerprint") == fingerprint, "PLAN_CONTENT_CHANGED", args.phase)
        phase["plan_fingerprint"] = fingerprint
        transitions(old, candidate, args.phase, order)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         prefix=".state-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(candidate, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        return {"status": "passed", "committed": True, "sequence": candidate["sequence"]}
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        lock.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--phase", required=True, choices=sorted(PHASES))
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--evidence", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--expected-sequence", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run(args)
    except Invalid as exc:
        result = {"status": "failed", "code": exc.code, "message": str(exc)}
    except (OSError, UnicodeError) as exc:
        result = {"status": "failed", "code": "IO_ERROR", "message": str(exc)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
