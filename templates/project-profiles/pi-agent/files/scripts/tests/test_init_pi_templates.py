from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS = REPO_ROOT / "skills/t-init/assets/pi"


def render_project(root: Path, typescript: str, node_types: str) -> None:
    package = (ASSETS / "package.json").read_text(encoding="utf-8")
    for token, value in (("PACKAGE_NAME", "pi-init-test"), ("TYPESCRIPT_VERSION", typescript), ("NODE_TYPES_VERSION", node_types)):
        package = package.replace("{{" + token + "}}", value)
    (root / "package.json").write_text(package, encoding="utf-8")
    (root / "extensions").mkdir()
    (root / "scripts").mkdir()
    shutil.copy2(ASSETS / "extension.ts", root / "extensions/index.ts")
    shutil.copy2(ASSETS / "tsconfig.json", root / "tsconfig.json")
    shutil.copy2(ASSETS / "pi-smoke.mjs", root / "scripts/pi-smoke.mjs")


class PiSmokePrerequisiteTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required for the smoke entry")
    def test_invalid_arguments_and_missing_root_fail_before_loading_a_host(self) -> None:
        with tempfile.TemporaryDirectory(prefix="t-tools-pi-init-preflight-") as tmp:
            root = Path(tmp)
            render_project(root, "7.0.2", "22.20.5")
            for args in (("missing",), (".", "extra")):
                result = subprocess.run(["node", "scripts/pi-smoke.mjs", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")
                self.assertNotEqual(result.returncode, 0)
                record = json.loads(result.stderr.strip().splitlines()[-1])
                self.assertEqual(record["status"], "failed")
                self.assertEqual(record["modelCalls"], "not_verified")

    @unittest.skipUnless(shutil.which("node"), "Node is required for the smoke entry")
    def test_missing_local_host_is_a_failure_not_an_install_attempt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="t-tools-pi-init-no-host-") as tmp:
            root = Path(tmp)
            render_project(root, "7.0.2", "22.20.5")
            result = subprocess.run(["node", "scripts/pi-smoke.mjs"], cwd=root, capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ERR_MODULE_NOT_FOUND", result.stderr)
            self.assertFalse((root / "node_modules").exists())


@unittest.skipUnless(os.environ.get("T_TOOLS_PI_INIT_INTEGRATION") == "1", "Set T_TOOLS_PI_INIT_INTEGRATION=1 to install and validate the real scaffold")
class PiInitScaffoldIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="t-tools-pi-init-integration-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.npm = shutil.which("npm") or shutil.which("npm.cmd")
        if not cls.npm:
            raise RuntimeError("npm is required for scaffold integration")
        version = subprocess.check_output(["node", "--version"], text=True).strip().lstrip("v")
        if tuple(map(int, version.split("."))) < (22, 19, 0):
            raise RuntimeError("Scaffold integration requires Node >=22.19.0; use an isolated compatible runtime")
        render_project(cls.root, "7.0.2", "22.20.5")
        result = subprocess.run([cls.npm, "install", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=cls.root, capture_output=True, text=True, encoding="utf-8", timeout=180)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)

    def smoke(self, *args: str) -> tuple[subprocess.CompletedProcess, dict]:
        result = subprocess.run(["node", "scripts/pi-smoke.mjs", *args], cwd=self.root, capture_output=True, text=True, encoding="utf-8", timeout=45)
        output = result.stdout if result.stdout.strip() else result.stderr
        return result, json.loads(output.strip().splitlines()[-1])

    def test_typecheck_and_published_resource_list(self) -> None:
        result = subprocess.run([self.npm, "run", "type-check"], cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        pack = subprocess.run([self.npm, "pack", "--dry-run", "--ignore-scripts", "--json"], cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(pack.returncode, 0, pack.stderr)
        files = {item["path"] for item in json.loads(pack.stdout)[0]["files"]}
        self.assertIn("extensions/index.ts", files)
        self.assertFalse(any(path.startswith(("node_modules/", "scripts/")) for path in files))

    def test_real_loader_and_repeated_runs_preserve_package_and_project_settings(self) -> None:
        config = self.root / ".pi/settings.json"
        config.parent.mkdir(exist_ok=True)
        before_config = '{"packages":["./missing-package-must-not-be-loaded"]}\n'
        config.write_text(before_config, encoding="utf-8")
        before_lock = (self.root / "package-lock.json").read_bytes()
        before_package = (self.root / "package.json").read_bytes()
        try:
            for _ in range(2):
                result, record = self.smoke()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(record["status"], "passed")
                self.assertEqual(len(record["extensions"]), 1)
                self.assertEqual(record["modelCalls"], "not_verified")
                self.assertEqual(record["sessionLifecycle"], "not_verified")
                self.assertEqual(record["diagnostics"], [])
            self.assertEqual(config.read_text(encoding="utf-8"), before_config)
            self.assertEqual((self.root / "package-lock.json").read_bytes(), before_lock)
            self.assertEqual((self.root / "package.json").read_bytes(), before_package)
        finally:
            config.unlink()

    def test_extension_load_failure_is_reported(self) -> None:
        entry = self.root / "extensions/index.ts"
        original = entry.read_bytes()
        try:
            entry.write_text('export default () => { throw new Error("init fixture failure"); };', encoding="utf-8")
            result, record = self.smoke()
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(record["status"], "failed")
            self.assertIn("init fixture failure", json.dumps(record["diagnostics"]))
        finally:
            entry.write_bytes(original)

    def test_empty_resource_root_does_not_pass(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root, prefix="empty-") as tmp:
            result, record = self.smoke(tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(record["reason"], "No resources discovered")

    def test_project_skill_resources_load_without_inventing_an_extension(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root, prefix="skill-project-") as tmp:
            resources = Path(tmp) / ".pi"
            skill = resources / "skills/review/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text('---\nname: review\ndescription: Read project context before reviewing changes.\n---\nRead AGENTS.md before review.\n', encoding="utf-8")
            result, record = self.smoke(str(resources))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(record["skills"], ["review"])
            self.assertEqual(record["extensions"], [])


if __name__ == "__main__":
    unittest.main()
