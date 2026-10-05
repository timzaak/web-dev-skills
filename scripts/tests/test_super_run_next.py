from __future__ import annotations

import importlib.util
import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "super-run-next.py"
SPEC = importlib.util.spec_from_file_location("super_run_next", SCRIPT)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def state_json(active: list[str], statuses: dict[str, str | None] | None = None) -> str:
    statuses = statuses or {}
    phases = {}
    for phase in active:
        status = statuses.get(phase)
        if status is not None:
            phases[phase] = {
                "status": status,
                "plan": f".ai/super-run/demo/{phase}.md",
                "tasks": {
                    name: {"status": status, "agent_spec": f"{phase}-{name}.md", "references": [], "evidence": [f"{phase}-{name}-report"]}
                    for name in ("dev", "accept")
                },
            }
    return json.dumps(
        {"feature": "demo", "current_phase": None, "active_phases": active, "phases": phases,
         "sources": {"design": {"main": ".ai/design/demo.md", "documents": [".ai/design/demo.md"], "fingerprint": "sha256:design"},
                     "requirements": [], "decisions": [], "research": []}},
        ensure_ascii=False,
    )


def pipeline_json(phases: dict | None = None) -> str:
    phases = copy.deepcopy(phases or {})
    for phase, steps in phases.items():
        steps["input_fingerprint"] = runner.input_fingerprint(json.loads(state_json([phase], {phase: "completed"})), phase)
    return json.dumps(
        {
            "feature": "demo",
            "chain": ["review", "simplify", "push"],
            "phases": phases,
        },
        ensure_ascii=False,
    )


class NextActionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.run_dir = self.root / ".ai" / "super-run" / "demo"
        self.addCleanup(self._tmp.cleanup)

    def run_cli(self, feature: str = "demo") -> dict:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = runner.main([feature, "--root", str(self.root), "--json"])
        result = json.loads(buffer.getvalue())
        self.assertEqual(code, 0 if result["status"] in ("ok", "done", "blocked") else 1)
        return result

    def test_no_state_requests_first_phase_planning(self) -> None:
        result = self.run_cli()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["action"], "plan_first_phase")

    def test_unplanned_phase_requests_run_phase(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend", "frontend"]))
        result = self.run_cli()
        self.assertEqual(result["action"], "run_phase")
        self.assertEqual(result["phase"], "backend")

    def test_rank_ordering_overrides_state_order(self) -> None:
        write(
            self.run_dir / ".state.json",
            state_json(
                ["web-demo", "frontend", "backend"],
                {"backend": "completed", "frontend": "in_progress"},
            ),
        )
        write(
            self.run_dir / ".pipeline.json",
            pipeline_json({"backend": {"simplify": {"status": "completed"}, "review": {"status": "completed"}, "push": {"status": "completed"}}}),
        )
        result = self.run_cli()
        self.assertEqual(result["action"], "run_phase")
        self.assertEqual(result["phase"], "frontend")
        self.assertEqual(result["ordered_active_phases"], ["backend", "frontend", "web-demo"])

    def test_blocked_phase_requests_condition_check(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend"], {"backend": "blocked"}))
        result = self.run_cli()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["action"], "check_blocked")
        self.assertIsNone(result["step"])
        write(self.run_dir / ".state.json", state_json(["backend"], {"backend": "pending"}))
        self.assertEqual(self.run_cli()["action"], "run_phase")

    def test_completed_phase_without_cursor_requests_review(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend"], {"backend": "completed"}))
        result = self.run_cli()
        self.assertEqual(result["action"], "review")
        self.assertEqual(result["phase"], "backend")

    def test_partial_cursor_continues_first_incomplete_step(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend"], {"backend": "completed"}))
        write(
            self.run_dir / ".pipeline.json",
            pipeline_json({"backend": {"review": {"status": "completed"}, "simplify": {"status": "failed"}, "push": {"status": "pending"}}}),
        )
        result = self.run_cli()
        self.assertEqual(result["action"], "simplify")
        self.assertEqual(result["phase"], "backend")

    def test_blocked_quality_step_requests_condition_check(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend"], {"backend": "completed"}))
        write(
            self.run_dir / ".pipeline.json",
            pipeline_json({"backend": {"review": {"status": "blocked"}, "simplify": {"status": "pending"}, "push": {"status": "pending"}}}),
        )
        result = self.run_cli()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["action"], "check_blocked")
        self.assertEqual(result["step"], "review")
        write(self.run_dir / ".pipeline.json", pipeline_json({"backend": {"review": {"status": "pending"}}}))
        self.assertEqual(self.run_cli()["action"], "review")

    def test_finished_chain_moves_to_next_phase(self) -> None:
        write(
            self.run_dir / ".state.json",
            state_json(["backend", "frontend"], {"backend": "completed", "frontend": "pending"}),
        )
        write(
            self.run_dir / ".pipeline.json",
            pipeline_json({"backend": {"simplify": {"status": "completed"}, "review": {"status": "completed"}, "push": {"status": "completed"}}}),
        )
        result = self.run_cli()
        self.assertEqual(result["action"], "run_phase")
        self.assertEqual(result["phase"], "frontend")

    def test_skipped_phase_skips_quality_chain(self) -> None:
        write(
            self.run_dir / ".state.json",
            state_json(["backend", "web-demo"], {"backend": "completed", "web-demo": "skipped"}),
        )
        result = self.run_cli()
        self.assertEqual(result["action"], "review")
        self.assertEqual(result["phase"], "backend")

    def test_all_complete_reports_done(self) -> None:
        write(
            self.run_dir / ".state.json",
            state_json(["backend", "frontend"], {"backend": "completed", "frontend": "skipped"}),
        )
        write(
            self.run_dir / ".pipeline.json",
            pipeline_json({"backend": {"simplify": {"status": "completed"}, "review": {"status": "completed"}, "push": {"status": "completed"}}}),
        )
        result = self.run_cli()
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["action"], "none")
        self.assertEqual(result["phase_summary"]["backend"]["chain"], "completed")
        self.assertEqual(result["phase_summary"]["frontend"]["chain"], "skipped")

    def test_corrupted_state_returns_error(self) -> None:
        write(self.run_dir / ".state.json", "{ not json")
        result = self.run_cli()
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["action"], "none")

    def test_foreign_phase_in_active_phases_returns_error(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend", "unknown-phase"]))
        result = self.run_cli()
        self.assertEqual(result["status"], "error")

    def test_invalid_cursor_chain_returns_error(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend"], {"backend": "completed"}))
        write(self.run_dir / ".pipeline.json", json.dumps({"feature": "demo", "chain": ["push"], "phases": {}}))
        result = self.run_cli()
        self.assertEqual(result["status"], "error")

    def test_invalid_feature_name_returns_error(self) -> None:
        for feature in ("../escape", "C:escape", "bad\x00name"):
            with self.subTest(feature=feature):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    code = runner.main([feature, "--root", str(self.root), "--json"])
                result = json.loads(buffer.getvalue())
                self.assertEqual(code, 1)
                self.assertEqual(result["status"], "error")

    def test_non_file_state_is_not_treated_as_missing(self) -> None:
        path = self.run_dir / ".state.json"
        path.mkdir(parents=True)
        self.assertEqual(self.run_cli()["status"], "error")
        self.assertTrue(path.is_dir())

    def test_reaccepted_phase_invalidates_old_quality_chain(self) -> None:
        state = json.loads(state_json(["backend"], {"backend": "pending"}))
        cursor = json.loads(pipeline_json({"backend": {step: {"status": "completed"} for step in runner.CHAIN}}))
        write(self.run_dir / ".state.json", json.dumps(state))
        write(self.run_dir / ".pipeline.json", json.dumps(cursor))
        self.assertEqual(self.run_cli()["action"], "run_phase")
        state = json.loads(state_json(["backend"], {"backend": "completed"}))
        state["phases"]["backend"]["validation_revision"] = 1
        write(self.run_dir / ".state.json", json.dumps(state))
        result = self.run_cli()
        self.assertEqual(result["action"], "reset_quality")
        cursor["phases"]["backend"] = {"input_fingerprint": result["input_fingerprint"]}
        write(self.run_dir / ".pipeline.json", json.dumps(cursor))
        self.assertEqual(self.run_cli()["action"], "review")

    def test_changed_design_invalidates_bound_quality_chain(self) -> None:
        state = json.loads(state_json(["backend"], {"backend": "completed"}))
        state["sources"]["design"]["fingerprint"] = "sha256:new-design"
        write(self.run_dir / ".state.json", json.dumps(state))
        write(self.run_dir / ".pipeline.json", pipeline_json({"backend": {step: {"status": "completed"} for step in runner.CHAIN}}))
        self.assertEqual(self.run_cli()["action"], "reset_quality")

    def test_legacy_cursor_requires_explicit_quality_reset(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend"], {"backend": "completed"}))
        write(self.run_dir / ".pipeline.json", json.dumps({"feature": "demo", "chain": list(runner.CHAIN), "phases": {"backend": {"review": {"status": "completed"}}}}))
        self.assertEqual(self.run_cli()["action"], "reset_quality")

    def test_orphan_cursor_returns_error(self) -> None:
        write(self.run_dir / ".pipeline.json", pipeline_json())
        self.assertEqual(self.run_cli()["status"], "error")

    def test_foreign_state_or_cursor_returns_error(self) -> None:
        for filename, content in ((".state.json", state_json(["backend"])), (".pipeline.json", pipeline_json())):
            with self.subTest(filename=filename):
                write(self.run_dir / ".state.json", state_json(["backend"]))
                write(self.run_dir / ".pipeline.json", pipeline_json())
                data = json.loads(content)
                data["feature"] = "another-feature"
                write(self.run_dir / filename, json.dumps(data))
                self.assertEqual(self.run_cli()["status"], "error")

    def test_malformed_state_returns_structured_error_and_preserves_file(self) -> None:
        base = json.loads(state_json(["backend"], {"backend": "completed"}))
        variants = []
        for active in ([None], [["backend"]], ["backend", "backend"]):
            data = copy.deepcopy(base)
            data["active_phases"] = active
            variants.append(data)
        for entry in (None, [], {"status": "completed"}):
            data = copy.deepcopy(base)
            data["phases"]["backend"] = entry
            variants.append(data)
        for field, value in (("status", "pending"), ("references", None), ("evidence", [None]), ("evidence", []), ("failures_without_progress", True)):
            data = copy.deepcopy(base)
            data["phases"]["backend"]["tasks"]["accept"][field] = value
            variants.append(data)
        data = copy.deepcopy(base)
        data["phases"]["backend"]["tasks"]["accept"]["status"] = "skipped"
        variants.append(data)
        data = copy.deepcopy(base)
        data["phases"]["backend"]["validation_revision"] = -1
        variants.append(data)
        for index, data in enumerate(variants):
            with self.subTest(index=index):
                content = json.dumps(data) + "\n"
                path = self.run_dir / ".state.json"
                write(path, content)
                self.assertEqual(self.run_cli()["status"], "error")
                self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_invalid_cursor_phase_or_counter_returns_error(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend"], {"backend": "completed"}))
        for phases in ({"unknown": {}}, {"frontend": {}}, {"backend": {"review": {"status": "failed", "failures_without_progress": -1}}}, {"backend": {"input_fingerprint": "sha256:" + "z" * 64}}, {"backend": {"push": {"status": "pending", "ci_session": "../escape"}}}):
            write(self.run_dir / ".pipeline.json", json.dumps({"feature": "demo", "chain": list(runner.CHAIN), "phases": phases}))
            self.assertEqual(self.run_cli()["status"], "error")


if __name__ == "__main__":
    unittest.main()
