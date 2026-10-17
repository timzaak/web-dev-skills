import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import demo_env


class ProjectEnvironmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "scripts").mkdir()
        patcher = patch.object(demo_env, "REPO_ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def hook(self, name, content):
        (self.root / "scripts" / name).write_text(content, encoding="utf-8")

    def test_missing_health_and_start_do_not_claim_success(self):
        self.assertFalse(demo_env.check_environment_health().healthy)
        logger = Mock()
        self.assertFalse(demo_env.start_environment(logger))
        self.assertIn("Missing project hook", logger.error.call_args.args[0])

    def test_real_project_hooks_run_from_project_root_and_health_is_required(self):
        self.hook("demo-start.py", "from pathlib import Path\nPath('started').write_text('yes')\n")
        self.hook("demo-health.py", "from pathlib import Path\nraise SystemExit(0 if Path('started').is_file() else 1)\n")
        self.hook("demo-stop.py", "from pathlib import Path\nPath('started').unlink(missing_ok=True)\n")
        self.assertFalse(demo_env.check_environment_health().healthy)
        self.assertTrue(demo_env.start_environment(Mock()))
        self.assertTrue(demo_env.stop_environment())
        self.assertFalse(demo_env.check_environment_health().healthy)

    def test_failed_start_and_unhealthy_after_start_are_failures(self):
        self.hook("demo-start.py", "raise SystemExit(4)\n")
        self.assertFalse(demo_env.start_environment(Mock()))
        self.hook("demo-start.py", "pass\n")
        self.hook("demo-health.py", "raise SystemExit(2)\n")
        self.assertFalse(demo_env.start_environment(Mock()))


if __name__ == "__main__":
    unittest.main()
