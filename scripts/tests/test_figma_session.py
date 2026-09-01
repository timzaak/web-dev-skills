from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("figma_session", REPO_ROOT / "scripts" / "figma-session.py")
assert SPEC and SPEC.loader
figma_session = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = figma_session
SPEC.loader.exec_module(figma_session)


class SessionTests(unittest.TestCase):
    def test_normalize_target_rejects_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            path = Path(outside) / "page.tsx"
            path.write_text("", encoding="utf-8")
            with self.assertRaises(ValueError):
                figma_session.normalize_target(Path(temp), path)

    def test_create_and_resolve_unique_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            target_path = project / "src" / "page.tsx"
            target_path.parent.mkdir()
            target_path.write_text("", encoding="utf-8")
            target = figma_session.normalize_target(project, Path("src/page.tsx"))
            created = figma_session.create_session(
                project, target, file_key="abc", node_id="1:2", url="https://figma/x",
            )
            index = figma_session.load_index(project / "memo" / "figma" / "index.json")
            result = figma_session.resolve(index, target)
            self.assertTrue(created["created"])
            self.assertEqual(result["status"], "unique")
            self.assertEqual(result["session"]["sessionId"], "abc-1-2")

    def test_create_defaults_to_assets_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            target_path = project / "page.tsx"
            target_path.write_text("", encoding="utf-8")
            figma_session.create_session(
                project, "page.tsx", file_key="abc", node_id="1:2", url="https://figma/x",
            )
            session = json.loads(
                (project / "memo" / "figma" / "abc-1-2" / "session.json").read_text(encoding="utf-8")
            )
            self.assertEqual(session["stage"], "assets")

    def test_create_with_motion_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            target_path = project / "page.tsx"
            target_path.write_text("", encoding="utf-8")
            figma_session.create_session(
                project, "page.tsx", file_key="abc", node_id="1:2",
                url="https://figma/x", stage="motion",
            )
            session = json.loads(
                (project / "memo" / "figma" / "abc-1-2" / "session.json").read_text(encoding="utf-8")
            )
            self.assertEqual(session["stage"], "motion")

    def test_multiple_active_sessions_are_ambiguous(self) -> None:
        index = {
            "version": 1,
            "targets": {"src/page.tsx": [
                {"sessionId": "one", "status": "active"},
                {"sessionId": "two", "status": "active"},
            ]},
        }
        result = figma_session.resolve(index, "src/page.tsx")
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(len(result["sessions"]), 2)

    def test_archived_sessions_do_not_resolve(self) -> None:
        index = {"version": 1, "targets": {"x": [{"sessionId": "old", "status": "archived"}]}}
        self.assertEqual(figma_session.resolve(index, "x")["status"], "missing")

    def test_archive_updates_target_association(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            target_path = project / "page.tsx"
            target_path.write_text("", encoding="utf-8")
            figma_session.create_session(
                project, "page.tsx", file_key="abc", node_id="1:2", url="https://figma/x",
            )
            result = figma_session.archive_session(project, "page.tsx", "abc-1-2")
            index = figma_session.load_index(project / "memo" / "figma" / "index.json")
            self.assertTrue(result["archived"])
            self.assertEqual(figma_session.resolve(index, "page.tsx")["status"], "missing")


if __name__ == "__main__":
    unittest.main()
