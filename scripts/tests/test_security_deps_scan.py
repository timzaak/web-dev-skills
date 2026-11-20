from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "security-deps-scan.py"
SPEC = importlib.util.spec_from_file_location("security_deps_scan", SCRIPT)
assert SPEC and SPEC.loader
scanner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scanner
SPEC.loader.exec_module(scanner)


TRIVY_REPORT = {
    "Results": [
        {
            "Target": "Cargo.lock",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "RUSTSEC-2023-0018",
                    "Severity": "CRITICAL",
                    "PkgName": "rustls",
                    "InstalledVersion": "0.20.0",
                    "FixedVersion": "0.20.8",
                }
            ],
        },
        {
            "Target": "package-lock.json",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2021-23337",
                    "Severity": "HIGH",
                    "PkgName": "lodash",
                    "InstalledVersion": "4.17.15",
                    "FixedVersion": "4.17.21",
                },
                {
                    "VulnerabilityID": "CVE-2020-8203",
                    "Severity": "HIGH",
                    "PkgName": "lodash",
                    "InstalledVersion": "4.17.15",
                    "FixedVersion": "",
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2020-8203",
                },
            ],
        },
    ]
}


def write(path: Path, content: str = "{}\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")


def run_scan_json(argv: list[str]) -> tuple[int, dict]:
    """Run scanner.main with stdout captured, returning (exit_code, parsed JSON)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = scanner.main(argv)
    return code, json.loads(buffer.getvalue())


class ManifestDetectionTests(unittest.TestCase):
    def test_supported_lockfiles_map_to_ecosystems(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / "package-lock.json")
            write(root / "apps" / "server" / "Cargo.lock")
            write(root / "pom.xml")
            write(root / "node_modules" / "dep" / "yarn.lock")  # must be skipped
            manifests = scanner.find_manifests(root)
            self.assertEqual(
                manifests,
                [
                    {"path": "apps/server/Cargo.lock", "ecosystem": "cargo"},
                    {"path": "package-lock.json", "ecosystem": "npm"},
                    {"path": "pom.xml", "ecosystem": "maven"},
                ],
            )

    def test_no_manifest_errors_before_docker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(scanner, "docker_available") as available:
                code, result = run_scan_json(["scan", temp, "--json"])
            self.assertEqual(code, 1)
            self.assertFalse(available.called)
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["findings"][0]["code"], "NO_MANIFEST")
            self.assertEqual(result["vulnerability_count"], 0)

    def test_bad_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            missing = str(Path(temp) / "nope")
            code, result = run_scan_json(["scan", missing, "--json"])
        self.assertEqual(code, 1)
        self.assertEqual(result["findings"][0]["code"], "BAD_TARGET")


class ScanResultTests(unittest.TestCase):
    def prepare(self, temp: str) -> Path:
        root = Path(temp)
        write(root / "package-lock.json")
        write(root / "Cargo.lock")
        return root

    def test_vulnerabilities_found_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            self.prepare(temp)
            with mock.patch.object(scanner, "docker_available", return_value=True), \
                 mock.patch.object(scanner, "run_trivy", return_value=(0, json.dumps(TRIVY_REPORT), "")):
                code, result = run_scan_json(["scan", temp, "--json"])
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["vulnerability_count"], 3)
        self.assertEqual(result["by_severity"], {"CRITICAL": 1, "HIGH": 2})
        first = result["vulnerabilities"][0]
        self.assertEqual((first["id"], first["ecosystem"]), ("RUSTSEC-2023-0018", "cargo"))
        unfixed = next(v for v in result["vulnerabilities"] if v["id"] == "CVE-2020-8203")
        self.assertIsNone(unfixed["fixed"])
        self.assertEqual(unfixed["url"], "https://avd.aquasec.com/nvd/cve-2020-8203")

    def test_clean_scan_exits_0(self) -> None:
        report = {"Results": [{"Target": "package-lock.json", "Vulnerabilities": None}]}
        with tempfile.TemporaryDirectory() as temp:
            self.prepare(temp)
            with mock.patch.object(scanner, "docker_available", return_value=True), \
                 mock.patch.object(scanner, "run_trivy", return_value=(0, json.dumps(report), "")):
                code, result = run_scan_json(["scan", temp, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(
            result["manifests"],
            [{"path": "Cargo.lock", "ecosystem": "cargo"}, {"path": "package-lock.json", "ecosystem": "npm"}],
        )

    def test_trivy_failure_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            self.prepare(temp)
            with mock.patch.object(scanner, "docker_available", return_value=True), \
                 mock.patch.object(scanner, "run_trivy", return_value=(1, "", "daemon boom")):
                code, result = run_scan_json(["scan", temp, "--json"])
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["findings"][0]["code"], "SCAN_FAILED")

    def test_no_docker_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            self.prepare(temp)
            with mock.patch.object(scanner, "docker_available", return_value=False):
                code, result = run_scan_json(["scan", temp, "--json"])
        self.assertEqual(code, 1)
        self.assertEqual(result["findings"][0]["code"], "NO_DOCKER")
        self.assertEqual(len(result["manifests"]), 2)


if __name__ == "__main__":
    unittest.main()
