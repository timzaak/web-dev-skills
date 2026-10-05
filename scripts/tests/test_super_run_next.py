from __future__ import annotations

import importlib.util
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
            phases[phase] = {"status": status}
    return json.dumps(
        {"feature": "demo", "current_phase": None, "active_phases": active, "phases": phases},
        ensure_ascii=False,
    )


def pipeline_json(phases: dict | None = None) -> str:
    return json.dumps(
        {
            "feature": "demo",
            "chain": ["review", "simplify", "push"],
            "phases": phases or {},
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

    def test_blocked_phase_stops_pipeline(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend"], {"backend": "blocked"}))
        result = self.run_cli()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["action"], "none")

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

    def test_blocked_quality_step_stops_pipeline(self) -> None:
        write(self.run_dir / ".state.json", state_json(["backend"], {"backend": "completed"}))
        write(
            self.run_dir / ".pipeline.json",
            pipeline_json({"backend": {"review": {"status": "blocked"}, "simplify": {"status": "pending"}, "push": {"status": "pending"}}}),
        )
        result = self.run_cli()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["action"], "none")

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
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = runner.main(["../escape", "--root", str(self.root), "--json"])
        result = json.loads(buffer.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
