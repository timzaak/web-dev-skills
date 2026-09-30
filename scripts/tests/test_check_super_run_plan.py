from __future__ import annotations

import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("check_super_run", REPO / "scripts/check-super-run-plan.py")
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class SuperRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.feature = "示例 feature"
        self.home = self.root / ".ai/super-run" / self.feature
        self.base = self.home / "backend/r1"
        self.candidate = self.home / ".state.next.json"
        self.main = self.root / ".ai/design" / f"{self.feature}.md"
        write(self.main, """# Design
### 2.5 设计覆盖矩阵
| ID | Design | API | Test | Files |
| --- | --- | --- | --- | --- |
| REQ-1 | backend | create | behavior test | src/a.rs |
### 4.2 交付端范围
| Stack | Doc | Status |
| --- | --- | --- |
| backend | backend.md | 适用 |
### 4.3 跨端契约
| Operation ID | Method | Path |
| --- | --- | --- |
| create | POST | /objects |
## 8. 文件影响范围
| File | Operation | Owner |
| --- | --- | --- |
| src/a.rs | CREATE | backend |
| web/a.ts | CREATE | frontend |
""")
        write(self.main.with_suffix("") / ".state.json", '{"status": "complete"}')
        write(self.main.with_suffix("") / "backend.md", "# Backend contract")
        write(self.base / "index.md", "# Backend\nScope, source trace, decisions, validation and rulings.\n")
        slots = {}
        for slot, item_id in (("dev", "BE-D01"), ("accept", "BE-A01")):
            path = self.base / slot / f"{item_id}-work.md"
            agent = f"backend-{slot}"
            write(path, f"""id: {item_id}
title: Work
agent: {agent}
## Goal
Complete this responsibility.
## Work
Read design, implement or inspect the requested behavior.
## Files
src/a.rs
## Validation
Run the real targeted command and record expected and actual results.
## Handoff
None
""")
            manifest = self.base / f"{slot}.md"
            write(manifest, f"""## Items
| id | title | agent | file |
| --- | --- | --- | --- |
| {item_id} | Work | {agent} | {self.rel(path)} |
""")
            slots[slot] = {"status": "pending", "manifest": self.rel(manifest), "items": {
                item_id: {"status": "pending", "file": self.rel(path), "agent": agent,
                          "attempt": 0, "failures_without_progress": 0, "evidence": []}}}
        self.state = {"schema_version": 2, "sequence": 1, "feature": self.feature,
                      "current_phase": "backend", "active_phases": ["backend", "frontend"],
                      "phases": {"backend": {"status": "pending", "revision": 1,
                       "index": self.rel(self.base / "index.md"),
                       "design_fingerprint": checker.design.design_fingerprint(self.main), "slots": slots}}}
        coverage = []
        for row in checker.inventory(self.main):
            frontend = row["kind"] == "impact" and row["content"][0].startswith("web/")
            entry = {"source_id": row["source_id"], "disposition": "other_phase" if frontend else "implement",
                     "items": [] if frontend else ["BE-D01"], "reason": "owner from design"}
            if frontend:
                entry["phase"] = "frontend"
            coverage.append(entry)
        write(self.base / "coverage.json", json.dumps(coverage))

    def rel(self, path):
        return path.relative_to(self.root).as_posix()

    def item(self, item_id="BE-D01"):
        return next(slot["items"][item_id] for slot in self.state["phases"]["backend"]["slots"].values()
                    if item_id in slot["items"])

    def sync(self):
        phase = self.state["phases"]["backend"]
        for slot in phase["slots"].values():
            slot["status"] = checker.aggregate(i["status"] for i in slot["items"].values())
        phase["status"] = checker.aggregate(slot["status"] for slot in phase["slots"].values())
        self.state["current_phase"] = None if phase["status"] in checker.TERMINAL else "backend"
        write(self.candidate, json.dumps(self.state))

    def call(self, *args, state_path=None):
        self.sync()
        out = io.StringIO()
        with redirect_stdout(out):
            status = checker.main([str(state_path or self.candidate), "--phase", "backend", "--json", *args])
        result = json.loads(out.getvalue())
        self.assertEqual(status, int(result["status"] == "failed"))
        return result

    def commit(self):
        result = self.call("--commit", "--expected-sequence", str(self.state["sequence"] - 1), "--evidence")
        self.assertEqual(result["status"], "passed", result)
        self.state["sequence"] += 1
        return result

    def start(self, item_id="BE-D01"):
        item = self.item(item_id)
        item["status"] = "in_progress"
        item["attempt"] += 1

    def finish(self, item_id="BE-D01"):
        item = self.item(item_id)
        item["status"] = "completed"
        log = self.root / "logs" / f"{item_id}.md"
        write(log, "command, cwd, exit=0, selected=1, expected=actual, input fingerprint")
        item["evidence"] = [self.rel(log)]
        if item_id == "BE-A01":
            item.update(acceptance_result="ACCEPTED", blocking_findings=0, report_path=self.rel(log))

    def test_full_lifecycle_and_repeated_read_do_not_reexecute(self):
        self.commit()
        for item_id in ("BE-D01", "BE-A01"):
            self.start(item_id)
            self.commit()
            self.finish(item_id)
            self.commit()
        target = self.home / ".state.json"
        before = target.read_bytes()
        for _ in range(2):
            result = self.call("--evidence", state_path=target)
            self.assertEqual(result, {"status": "passed", "next_item": None})
        self.assertEqual(target.read_bytes(), before)
        self.assertIsNone(json.loads(before)["current_phase"])

    def test_inventory_and_other_phase_coverage_need_no_other_plan(self):
        result = self.call("--inventory")
        self.assertEqual(len(result["sources"]), 4)
        self.assertEqual(self.call()["status"], "passed")
        self.assertFalse((self.home / "frontend").exists())

    def test_in_progress_is_returned_as_recovery_entry(self):
        self.commit()
        self.start()
        self.commit()
        self.assertEqual(self.call(state_path=self.home / ".state.json")["next_item"], "BE-D01")
        self.item().update(status="pending", reason="worker gone; inspected workspace and remaining validation")
        self.commit()
        self.start()
        self.commit()
        self.assertEqual(self.item()["attempt"], 2)

    def test_accept_rejection_reopens_dev_then_test_and_accept(self):
        self.commit()
        self.start()
        self.commit()
        self.finish()
        self.commit()
        self.start("BE-A01")
        self.commit()
        self.item("BE-A01").update(status="failed", last_error="business assertion failed")
        self.commit()
        self.item().update(status="pending", reason="accept rejected behavior")
        self.item("BE-A01").update(status="pending", reason="requires fresh acceptance after repair")
        self.commit()
        self.assertEqual(self.call()["next_item"], "BE-D01")

    def test_illegal_success_transition_keeps_previous_snapshot(self):
        self.commit()
        target = self.home / ".state.json"
        before = target.read_bytes()
        self.item()["attempt"] = 1
        self.finish()
        result = self.call("--commit", "--expected-sequence", "1", "--evidence")
        self.assertEqual(result["code"], "TRANSITION_INVALID")
        self.assertEqual(target.read_bytes(), before)

    def test_cannot_dispatch_accept_before_dev(self):
        self.commit()
        self.start("BE-A01")
        result = self.call("--commit", "--expected-sequence", "1")
        self.assertEqual(result["code"], "PREDECESSOR_UNFINISHED")

    def test_stale_checkpoint_and_active_lock_are_rejected(self):
        self.commit()
        self.assertEqual(self.call("--commit", "--expected-sequence", "0")["code"], "SEQUENCE_CONFLICT")
        write(self.home / ".state.lock", "existing controller")
        self.assertEqual(self.call("--commit", "--expected-sequence", "1")["code"], "STATE_LOCKED")
        self.assertEqual((self.home / ".state.lock").read_text(), "existing controller")

    def test_io_failure_preserves_previous_snapshot_and_releases_lock(self):
        self.commit()
        target = self.home / ".state.json"
        before = target.read_bytes()
        self.start()
        with patch.object(checker.os, "replace", side_effect=OSError("disk write failed")):
            result = self.call("--commit", "--expected-sequence", "1")
        self.assertEqual(result["code"], "IO_ERROR")
        self.assertEqual(target.read_bytes(), before)
        self.assertFalse((self.home / ".state.lock").exists())
        self.assertEqual(list(self.home.glob(".state-*.tmp")), [])

    def test_missing_item_or_orphan_is_rejected(self):
        path = self.root / self.item()["file"]
        content = path.read_text(encoding="utf-8")
        path.unlink()
        self.assertEqual(self.call()["code"], "ARTIFACT_MISSING")
        write(path, content)
        write(self.base / "dev/orphan.md", content)
        self.assertEqual(self.call()["code"], "ORPHAN_ITEM")

    def test_manifest_duplicates_and_missing_source_mapping_fail(self):
        manifest = self.base / "dev.md"
        content = manifest.read_text(encoding="utf-8")
        write(manifest, content + content.splitlines()[-1] + "\n")
        self.assertEqual(self.call()["code"], "MANIFEST_ITEMS_MISMATCH")
        write(manifest, content)
        coverage = json.loads((self.base / "coverage.json").read_text())
        write(self.base / "coverage.json", json.dumps(coverage[:-1]))
        self.assertEqual(self.call()["code"], "COVERAGE_INCOMPLETE")

    def test_fingerprint_change_or_incomplete_design_blocks(self):
        write(self.main, self.main.read_text(encoding="utf-8") + "\nChanged design\n")
        self.assertEqual(self.call()["code"], "FINGERPRINT_MISMATCH")
        write(self.main.with_suffix("") / ".state.json", '{"status":"in_progress"}')
        self.assertEqual(self.call()["code"], "DESIGN_INCOMPLETE")

    def test_missing_evidence_and_invalid_acceptance_block_completion(self):
        self.item()["attempt"] = 1
        self.finish()
        (self.root / self.item()["evidence"][0]).unlink()
        self.assertEqual(self.call("--evidence")["code"], "EVIDENCE_MISSING")
        self.finish()
        self.item("BE-A01")["attempt"] = 1
        self.finish("BE-A01")
        self.item("BE-A01")["blocking_findings"] = 1
        self.assertEqual(self.call("--evidence")["code"], "ACCEPTANCE_INVALID")

    def test_aggregate_error_is_not_silently_corrected(self):
        self.sync()
        self.state["phases"]["backend"]["status"] = "completed"
        with self.assertRaisesRegex(checker.Invalid, "backend"):
            checker.shape(self.state, self.feature)

    def test_legacy_or_corrupt_state_is_preserved(self):
        target = self.home / ".state.json"
        for raw, code in [('{"feature":"legacy"}', "SCHEMA_VERSION"), ('{broken', "JSON_INVALID")]:
            write(target, raw)
            self.assertEqual(self.call("--commit", "--expected-sequence", "0")["code"], code)
            self.assertEqual(target.read_text(), raw)

    def test_escaping_item_path_is_rejected(self):
        self.item()["file"] = "../outside.md"
        manifest = self.base / "dev.md"
        text = manifest.read_text(encoding="utf-8")
        text = text.replace(self.rel(self.base / "dev/BE-D01-work.md"), "../outside.md")
        write(manifest, text)
        self.assertEqual(self.call()["code"], "PATH_OUTSIDE_SCOPE")

    def test_retry_limit_persists_across_reentry(self):
        self.commit()
        self.start()
        self.commit()
        self.item().update(status="failed", last_error="same error", failures_without_progress=3)
        self.commit()
        self.start()
        self.assertEqual(self.call("--commit", "--expected-sequence", "3")["code"], "RETRY_LIMIT")

    def test_source_change_allows_stopping_old_attempt_but_not_success(self):
        self.commit()
        self.start()
        self.commit()
        write(self.main, self.main.read_text(encoding="utf-8").replace("REQ-1", "REQ-2"))
        self.finish()
        self.assertEqual(self.call("--commit", "--expected-sequence", "2")["code"], "FINGERPRINT_MISMATCH")
        self.item().update(status="pending", reason="worker stopped; new design needs replan", evidence=[])
        self.commit()
        self.assertEqual(self.call()["code"], "FINGERPRINT_MISMATCH")

    def test_commit_always_checks_completion_evidence(self):
        self.commit()
        self.start()
        self.commit()
        self.item()["status"] = "completed"
        self.assertEqual(self.call("--commit", "--expected-sequence", "2")["code"], "EVIDENCE_MISSING")

    def test_executable_plan_is_immutable_but_handoff_can_record_evidence(self):
        self.commit()
        path = self.root / self.item()["file"]
        original = path.read_text(encoding="utf-8")
        write(path, original + "\nExecution evidence in Handoff.\n")
        self.start()
        self.commit()
        write(path, original.replace("Complete this responsibility.", "Change business scope."))
        self.item().update(status="failed", last_error="changed plan")
        self.assertEqual(self.call("--commit", "--expected-sequence", "2")["code"], "PLAN_CONTENT_CHANGED")

    def test_invalid_status_type_returns_structured_error(self):
        self.item()["status"] = []
        write(self.candidate, json.dumps(self.state))
        out = io.StringIO()
        with redirect_stdout(out):
            result = checker.main([str(self.candidate), "--phase", "backend", "--json"])
        self.assertEqual(result, 1)
        self.assertEqual(json.loads(out.getvalue())["code"], "STATUS_INVALID")

    def test_role_repair_item_requires_failure_evidence_and_an_existing_origin(self):
        original = self.item()
        repair = copy.deepcopy(original)
        path = self.base / "dev/BE-D02-repair.md"
        content = (self.root / original["file"]).read_text(encoding="utf-8")
        write(path, content.replace("BE-D01", "BE-D02").replace("backend-dev", "frontend-dev"))
        log = self.root / "logs/failure.md"
        write(log, "Reproducible failure in the same authorized feature.")
        repair.update(file=self.rel(path), agent="frontend-dev", repair_for="BE-D01",
                      reason="client defect identified by failure evidence", repair_evidence=[self.rel(log)])
        slot = self.state["phases"]["backend"]["slots"]["dev"]
        slot["items"]["BE-D02"] = repair
        manifest = self.base / "dev.md"
        rows = manifest.read_text(encoding="utf-8").splitlines()
        rows.insert(3, f"| BE-D02 | Work | frontend-dev | {self.rel(path)} |")
        write(manifest, "\n".join(rows) + "\n")
        self.assertEqual(self.call()["status"], "passed")
        log.unlink()
        self.assertEqual(self.call()["code"], "REPAIR_EVIDENCE_MISSING")
        write(log, "Failure.")
        repair["repair_for"] = "BE-D99"
        self.assertEqual(self.call()["code"], "REPAIR_INVALID")

    def test_replan_requires_new_revision_and_keeps_old_artifacts(self):
        self.commit()
        old_file = self.root / self.item()["file"]
        old_bytes = old_file.read_bytes()
        new_base = self.home / "backend/r2"
        for path in self.base.rglob("*"):
            if path.is_file():
                write(new_base / path.relative_to(self.base), path.read_text(encoding="utf-8").replace("/r1/", "/r2/"))
        phase = json.loads(json.dumps(self.state["phases"]["backend"]).replace("/r1/", "/r2/"))
        phase.update(revision=2, replan_reason="updated responsibility boundary")
        self.state["phases"]["backend"] = phase
        self.commit()
        self.assertEqual(old_file.read_bytes(), old_bytes)
        self.assertEqual(json.loads((self.home / ".state.json").read_text())["phases"]["backend"]["revision"], 2)


if __name__ == "__main__":
    unittest.main()
