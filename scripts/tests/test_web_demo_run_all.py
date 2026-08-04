from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

SPEC = importlib.util.spec_from_file_location("demo_run_all", SCRIPTS_DIR / "web-demo-run-all.py")
assert SPEC and SPEC.loader
demo_run_all = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = demo_run_all
SPEC.loader.exec_module(demo_run_all)


def payload(*, status: str = "running", entries: list[dict[str, object]] | None = None) -> dict[str, object]:
    files = ["demo/e2e/a.e2e.ts", "demo/e2e/b.e2e.ts"]
    completed = entries or []
    return {
        "batch_status": status,
        "discovered_files": files,
        "entries": completed,
        "current_index": len(completed),
        "current_file": "",
    }


class ResumeStateTests(unittest.TestCase):
    def test_completed_batch_cannot_continue(self) -> None:
        state = payload(status="completed", entries=[{"test_file": "demo/e2e/a.e2e.ts", "status": "failed"}])
        with self.assertRaisesRegex(ValueError, "not running"):
            demo_run_all.determine_resume_index(state)

    def test_resume_uses_next_unfinished_file_not_last_failure(self) -> None:
        state = payload(entries=[{"test_file": "demo/e2e/a.e2e.ts", "status": "failed"}])
        self.assertEqual(demo_run_all.determine_resume_index(state), 1)

    def test_entries_must_be_discovered_prefix(self) -> None:
        state = payload(entries=[{"test_file": "demo/e2e/b.e2e.ts", "status": "passed"}])
        with self.assertRaisesRegex(ValueError, "completed prefix"):
            demo_run_all.determine_resume_index(state)


class ProgressCommandTests(unittest.TestCase):
    def test_checkpoint_and_record_derive_progress_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "batch.json"
            report.write_text(json.dumps(payload()), encoding="utf-8")
            checkpoint_args = Namespace(json=report, index=0)
            self.assertEqual(demo_run_all.cmd_checkpoint(checkpoint_args), 0)

            record_args = Namespace(
                json=report,
                status="passed",
                exit_code=0,
                duration=1.25,
                run_id="run-a",
                logs="demo/logs/a",
                error="ignored",
                fixed=True,
            )
            self.assertEqual(demo_run_all.cmd_record(record_args), 0)
            saved = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(saved["current_index"], 1)
            self.assertEqual(saved["current_file"], "")
            self.assertEqual(saved["passed_files"], 1)
            self.assertEqual(saved["total_duration"], 1.25)
            self.assertEqual(saved["entries"][0]["test_file"], "demo/e2e/a.e2e.ts")
            self.assertEqual(saved["entries"][0]["error"], "")

    def test_block_preserves_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "batch.json"
            state = payload()
            state["current_file"] = "demo/e2e/a.e2e.ts"
            report.write_text(json.dumps(state), encoding="utf-8")
            self.assertEqual(
                demo_run_all.cmd_block(Namespace(json=report, error="restart failed")),
                0,
            )
            saved = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(saved["current_file"], "demo/e2e/a.e2e.ts")
            self.assertEqual(saved["entries"], [])
            self.assertEqual(saved["last_error"], "restart failed")

class FinalizeTests(unittest.TestCase):
    def test_incomplete_batch_is_not_finalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "batch.json"
            report.write_text(json.dumps(payload()), encoding="utf-8")
            with patch.object(demo_run_all, "REPO_ROOT", Path(temp_dir)):
                result = demo_run_all.cmd_finalize(Namespace(json=report))
            self.assertEqual(result, 1)
            saved = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(saved["batch_status"], "running")

    def test_invalid_entry_order_is_not_finalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "batch.json"
            state = payload(entries=[
                {"test_file": "demo/e2e/b.e2e.ts", "status": "passed"},
                {"test_file": "demo/e2e/a.e2e.ts", "status": "passed"},
            ])
            report.write_text(json.dumps(state), encoding="utf-8")
            with patch.object(demo_run_all, "REPO_ROOT", Path(temp_dir)):
                result = demo_run_all.cmd_finalize(Namespace(json=report))
            self.assertEqual(result, 1)

    def test_complete_valid_batch_is_finalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "batch.json"
            state = payload(entries=[
                {"test_file": "demo/e2e/a.e2e.ts", "status": "passed", "exit_code": 0},
                {"test_file": "demo/e2e/b.e2e.ts", "status": "failed", "exit_code": 1},
            ])
            state["markdown_report"] = "batch.md"
            state["total_duration"] = 3.5
            report.write_text(json.dumps(state), encoding="utf-8")
            with patch.object(demo_run_all, "REPO_ROOT", root):
                result = demo_run_all.cmd_finalize(Namespace(json=report))
            self.assertEqual(result, 1)
            saved = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(saved["batch_status"], "completed")
            self.assertEqual(saved["total_files"], 2)
            self.assertTrue((root / "batch.md").exists())


class ScanInitTests(unittest.TestCase):
    def test_scan_init_populates_one_entry_per_discovered_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "batch.json"
            report.write_text(json.dumps(payload()), encoding="utf-8")
            args = Namespace(
                json=report, file="", status="passed", exit_code=0, duration=0.0,
                run_id="", logs="", force=False, scan_run_id="run-all-scan-x",
            )
            self.assertEqual(demo_run_all.cmd_scan(args), 0)
            saved = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(saved["scan_run_id"], "run-all-scan-x")
            results = saved["scan_results"]
            self.assertEqual(len(results), 2)
            self.assertEqual([entry["test_file"] for entry in results],
                             ["demo/e2e/a.e2e.ts", "demo/e2e/b.e2e.ts"])
            self.assertTrue(all(entry["status"] == "pending" for entry in results))

    def test_scan_init_idempotent_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "batch.json"
            state = payload()
            state["scan_results"] = [{"test_file": "demo/e2e/a.e2e.ts", "status": "passed"}]
            report.write_text(json.dumps(state), encoding="utf-8")
            args = Namespace(
                json=report, file="", status="passed", exit_code=0, duration=0.0,
                run_id="", logs="", force=False, scan_run_id="ignored",
            )
            self.assertEqual(demo_run_all.cmd_scan(args), 0)
            # Idempotent: pre-existing results are not wiped.
            saved = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(len(saved["scan_results"]), 1)


class ScanRecordTests(unittest.TestCase):
    def test_scan_record_updates_one_file_and_leaves_others_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "batch.json"
            state = payload()
            state["scan_results"] = [
                {"test_file": "demo/e2e/a.e2e.ts", "status": "pending"},
                {"test_file": "demo/e2e/b.e2e.ts", "status": "pending"},
            ]
            report.write_text(json.dumps(state), encoding="utf-8")
            args = Namespace(
                json=report, file="demo/e2e/a.e2e.ts", status="failed", exit_code=1,
                duration=2.0, run_id="run-all-scan-x-a", logs="demo/logs/a",
                force=False, scan_run_id="",
            )
            self.assertEqual(demo_run_all.cmd_scan(args), 0)
            saved = json.loads(report.read_text(encoding="utf-8"))
            results = saved["scan_results"]
            self.assertEqual(results[0]["status"], "failed")
            self.assertEqual(results[0]["run_id"], "run-all-scan-x-a")
            self.assertEqual(results[1]["status"], "pending")

    def test_scan_record_rejects_unknown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "batch.json"
            state = payload()
            state["scan_results"] = [{"test_file": "demo/e2e/a.e2e.ts", "status": "pending"}]
            report.write_text(json.dumps(state), encoding="utf-8")
            args = Namespace(
                json=report, file="demo/e2e/missing.e2e.ts", status="failed", exit_code=1,
                duration=0.0, run_id="x", logs="", force=False, scan_run_id="",
            )
            self.assertEqual(demo_run_all.cmd_scan(args), 1)


class ClusterTests(unittest.TestCase):
    @staticmethod
    def _make_log(root: Path, run_id: str, *, case_title: str, error_line: str,
                  selector: str = "") -> None:
        log_dir = root / "demo" / "test-results" / "runs" / run_id
        log_dir.mkdir(parents=True, exist_ok=True)
        lines = [
            f"  ✗ 1 demo/e2e/x.e2e.ts:8:1 › {case_title} (1.2s)",
        ]
        if error_line:
            lines.append(f"      {error_line}")
        if selector:
            lines.append(f"    page.click('{selector}')")
        (log_dir / "playwright-output.log").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_same_selector_failure_groups_into_one_cluster(self) -> None:
        failed = [
            {"test_file": "demo/e2e/a.e2e.ts", "status": "failed", "run_id": "run-a"},
            {"test_file": "demo/e2e/b.e2e.ts", "status": "failed", "run_id": "run-b"},
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._make_log(root, "run-a", case_title="login button visible",
                           error_line="Error: locator.click: Timeout 30000ms exceeded",
                           selector="[data-testid=\"login-btn\"]")
            self._make_log(root, "run-b", case_title="submit form",
                           error_line="TimeoutError: locator.click: Timeout 30000ms exceeded",
                           selector="[data-testid=\"login-btn\"]")
            with patch.object(demo_run_all, "REPO_ROOT", root):
                clusters, unclusterable = demo_run_all.build_clusters(
                    failed, root / "demo" / "test-results" / "runs")
            self.assertEqual(len(clusters), 1)
            cluster = clusters[0]
            self.assertIn("timeout", cluster["fingerprint"])
            self.assertEqual(sorted(cluster["affected_files"]),
                             ["demo/e2e/a.e2e.ts", "demo/e2e/b.e2e.ts"])
            self.assertEqual(len(cluster["affected_cases"]), 2)
            self.assertEqual(unclusterable, [])

    def test_distinct_fingerprints_form_separate_clusters(self) -> None:
        failed = [
            {"test_file": "demo/e2e/a.e2e.ts", "status": "failed", "run_id": "run-a"},
            {"test_file": "demo/e2e/b.e2e.ts", "status": "failed", "run_id": "run-b"},
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._make_log(root, "run-a", case_title="c1",
                           error_line="Error: selector not found",
                           selector="[data-testid=\"x\"]")
            self._make_log(root, "run-b", case_title="c2",
                           error_line="Error: GET /api/users failed",
                           selector="/api/users")
            with patch.object(demo_run_all, "REPO_ROOT", root):
                clusters, unclusterable = demo_run_all.build_clusters(
                    failed, root / "demo" / "test-results" / "runs")
            self.assertEqual(len(clusters), 2)
            self.assertEqual(unclusterable, [])

    def test_missing_log_becomes_unclusterable_not_silently_dropped(self) -> None:
        failed = [
            {"test_file": "demo/e2e/a.e2e.ts", "status": "failed", "run_id": "missing-run"},
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch.object(demo_run_all, "REPO_ROOT", root):
                clusters, unclusterable = demo_run_all.build_clusters(
                    failed, root / "demo" / "test-results" / "runs")
            self.assertEqual(clusters, [])
            self.assertEqual(len(unclusterable), 1)
            self.assertEqual(unclusterable[0]["reason"], "log not found")


if __name__ == "__main__":
    unittest.main()
