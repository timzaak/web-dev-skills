from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
SPEC = importlib.util.spec_from_file_location(
    "figma_measure", SCRIPTS_DIR / "figma-measure.py"
)
assert SPEC and SPEC.loader
figma_measure = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = figma_measure
SPEC.loader.exec_module(figma_measure)


def make_spec(probes: list[dict]) -> dict:
    return {
        "source": {"url": "https://example.com/card"},
        "probeSelectors": probes,
    }


class ClassifyNumericTests(unittest.TestCase):
    def test_px_under_2_is_pass(self) -> None:
        status, delta = figma_measure.classify_delta("fontSize", 24, 24 + 1)
        self.assertEqual(status, "PASS")
        self.assertAlmostEqual(delta, 1.0)

    def test_px_string_values_parsed(self) -> None:
        status, _ = figma_measure.classify_delta("gap", "16px", "14px")
        self.assertEqual(status, "WARN")  # delta 2.0 -> WARN (2 <= d < 4)

    def test_px_4_or_more_is_fail(self) -> None:
        status, delta = figma_measure.classify_delta("width", 320, 325)
        self.assertEqual(status, "FAIL")
        self.assertAlmostEqual(delta, 5.0)

    def test_px_exactly_4_is_fail(self) -> None:
        status, _ = figma_measure.classify_delta("height", 48, 52)
        self.assertEqual(status, "FAIL")

    def test_px_exactly_2_is_warn(self) -> None:
        # delta == 2.0 falls in WARN band [2, 4)
        status, _ = figma_measure.classify_delta("padding", 16, 18)
        self.assertEqual(status, "WARN")

    def test_unparseable_is_missing(self) -> None:
        status, delta = figma_measure.classify_delta("fontSize", "auto", 16)
        self.assertEqual(status, "MISSING")
        self.assertIsNone(delta)


class ClassifyDurationTests(unittest.TestCase):
    def test_equal_ms_is_pass(self) -> None:
        status, _ = figma_measure.classify_delta("transitionDuration", "200ms", "200ms")
        self.assertEqual(status, "PASS")

    def test_seconds_normalized(self) -> None:
        status, _ = figma_measure.classify_delta("animationDuration", "0.2s", "200ms")
        self.assertEqual(status, "PASS")

    def test_50ms_or_more_is_fail(self) -> None:
        status, _ = figma_measure.classify_delta("transitionDuration", "200ms", "260ms")
        self.assertEqual(status, "FAIL")

    def test_under_50ms_delta_is_warn(self) -> None:
        status, _ = figma_measure.classify_delta("transitionDuration", "200ms", "230ms")
        self.assertEqual(status, "WARN")


class ClassifyColorTests(unittest.TestCase):
    def test_hex_match(self) -> None:
        status, _ = figma_measure.classify_delta("color", "#1d4ed8", "#1D4ED8")
        self.assertEqual(status, "PASS")

    def test_rgb_hex_equivalent(self) -> None:
        status, _ = figma_measure.classify_delta("backgroundColor", "#1d4ed8", "rgb(29, 78, 216)")
        self.assertEqual(status, "PASS")

    def test_mismatch_is_fail(self) -> None:
        status, _ = figma_measure.classify_delta("color", "#000000", "rgb(255, 255, 255)")
        self.assertEqual(status, "FAIL")

    def test_short_hex_matches_long_hex(self) -> None:
        status, _ = figma_measure.classify_delta("color", "#fff", "rgb(255 255 255)")
        self.assertEqual(status, "PASS")

    def test_alpha_difference_fails(self) -> None:
        status, _ = figma_measure.classify_delta(
            "backgroundColor", "#1d4ed833", "rgba(29, 78, 216, 1)",
        )
        self.assertEqual(status, "FAIL")


class ClassifyEnumTests(unittest.TestCase):
    def test_font_weight_match(self) -> None:
        status, _ = figma_measure.classify_delta("fontWeight", 600, "600")
        self.assertEqual(status, "PASS")

    def test_font_weight_mismatch(self) -> None:
        status, _ = figma_measure.classify_delta("fontWeight", 600, "500")
        self.assertEqual(status, "FAIL")


class ComputeDeltaTests(unittest.TestCase):
    def test_converged_when_no_fail(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24, "fontWeight": 600}},
        ])
        actuals = {"title": {"fontSize": 24, "fontWeight": "600"}}
        report = figma_measure.compute_delta(spec, actuals)
        self.assertTrue(report.converged)
        self.assertEqual(report.failed, 0)
        self.assertEqual(report.passed, 2)

    def test_not_converged_when_fail_present(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        actuals = {"title": {"fontSize": 30}}
        report = figma_measure.compute_delta(spec, actuals)
        self.assertFalse(report.converged)
        self.assertEqual(report.failed, 1)

    def test_missing_probe_recorded(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        report = figma_measure.compute_delta(spec, {})
        self.assertFalse(report.converged)
        self.assertEqual(report.missing, 1)

    def test_probe_error_recorded(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24, "color": "#000"}},
        ])
        actuals = {"title": {"__error": "element not found: .t"}}
        report = figma_measure.compute_delta(spec, actuals)
        self.assertEqual(report.errored, 2)
        self.assertFalse(report.converged)

    def test_warn_does_not_block_convergence(self) -> None:
        spec = make_spec([
            {"name": "gap", "selector": ".g", "expect": {"gap": 16}},
        ])
        actuals = {"gap": {"gap": 18}}  # delta 2 -> WARN
        report = figma_measure.compute_delta(spec, actuals)
        self.assertTrue(report.converged)
        self.assertEqual(report.warned, 1)

    def test_declared_conflict_does_not_block_convergence(self) -> None:
        spec = make_spec([
            {"name": "card", "selector": ".card", "expect": {"padding": 13}},
        ])
        actuals = {"card": {"padding": 16}}
        conflicts = [{
            "name": "card", "prop": "padding", "spec": 13,
            "projectValue": 16, "token": "space-4", "reason": "existing token",
        }]
        report = figma_measure.compute_delta(spec, actuals, conflicts=conflicts)
        self.assertTrue(report.converged)
        self.assertEqual(report.conflicted, 1)
        self.assertEqual(report.results[0].status, "CONFLICT")

    def test_conflict_does_not_hide_unexpected_actual_value(self) -> None:
        spec = make_spec([
            {"name": "card", "selector": ".card", "expect": {"padding": 13}},
        ])
        conflicts = [{
            "name": "card", "prop": "padding", "spec": 13,
            "projectValue": 16, "token": "space-4", "reason": "existing token",
        }]
        report = figma_measure.compute_delta(
            spec, {"card": {"padding": 20}}, conflicts=conflicts,
        )
        self.assertFalse(report.converged)
        self.assertEqual(report.results[0].status, "FAIL")

    def test_missing_element_is_counted_as_missing(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".title", "expect": {"fontSize": 24}},
        ])
        actuals = {"title": {"__missing": "element not found"}}
        report = figma_measure.compute_delta(spec, actuals)
        self.assertEqual(report.missing, 1)
        self.assertEqual(report.errored, 0)

    def test_report_target_is_measured_url(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".title", "expect": {"fontSize": 24}},
        ])
        report = figma_measure.compute_delta(
            spec, {"title": {"fontSize": 24}}, target_url="http://localhost/page",
        )
        self.assertEqual(report.target, "http://localhost/page")

    def test_to_dict_shape(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        actuals = {"title": {"fontSize": 24}}
        report = figma_measure.compute_delta(spec, actuals)
        d = report.to_dict()
        self.assertIn("summary", d)
        self.assertEqual(d["summary"]["total"], 1)
        self.assertEqual(len(d["results"]), 1)
        self.assertEqual(d["results"][0]["name"], "title")


@dataclass
class FakeCompleted:
    returncode: int
    stdout: str
    stderr: str


class MeasureTests(unittest.TestCase):
    def test_measure_parses_probe_stdout(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        captured = {}

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            captured["cmd"] = cmd
            captured["env"] = env
            # Read what the script wrote so we can assert probes were injected.
            probe_file = Path(str(cwd)) / ".ai" / "figma" / "_probe.js"
            captured["script"] = probe_file.read_text(encoding="utf-8")
            return FakeCompleted(0, json.dumps({"title": {"fontSize": 24}}), "")

        with tempfile.TemporaryDirectory() as temp:
            cwd = Path(temp)
            actuals = figma_measure.measure(
                "http://localhost:3000/x", spec, cwd=cwd,
                runner=fake_runner, node_path="/usr/bin/node",
            )
        self.assertEqual(actuals, {"title": {"fontSize": 24}})
        self.assertEqual(captured["env"]["FIGMA_MEASURE_URL"], "http://localhost:3000/x")
        self.assertIn("PATH", captured["env"])
        self.assertIn("require('playwright')", captured["script"])
        # probeSelectors content is embedded
        self.assertIn('"selector": ".t"', captured["script"])

    def test_measure_returns_error_on_nonzero(self) -> None:
        spec = make_spec([])

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            return FakeCompleted(1, "", "boom")

        with tempfile.TemporaryDirectory() as temp:
            actuals = figma_measure.measure(
                "http://x", spec, cwd=Path(temp),
                runner=fake_runner, node_path="/usr/bin/node",
            )
        self.assertIn("__probe_error__", actuals)
        self.assertEqual(actuals["__probe_error__"]["__error"], "boom")

    def test_measure_returns_error_on_bad_json(self) -> None:
        spec = make_spec([])

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            return FakeCompleted(0, "not json", "")

        with tempfile.TemporaryDirectory() as temp:
            actuals = figma_measure.measure(
                "http://x", spec, cwd=Path(temp),
                runner=fake_runner, node_path="/usr/bin/node",
            )
        self.assertIn("__probe_error__", actuals)
        self.assertIn("invalid JSON", actuals["__probe_error__"]["__error"])

    def test_measure_cleans_up_probe_file(self) -> None:
        spec = make_spec([])

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            return FakeCompleted(0, "{}", "")

        with tempfile.TemporaryDirectory() as temp:
            cwd = Path(temp)
            figma_measure.measure(
                "http://x", spec, cwd=cwd,
                runner=fake_runner, node_path="/usr/bin/node",
            )
            self.assertFalse((cwd / ".ai" / "figma" / "_probe.js").exists())

    def test_measure_passes_viewport_and_screenshot_to_probe(self) -> None:
        spec = make_spec([])
        captured = {}

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            captured["env"] = env
            captured["script"] = (Path(cwd) / ".ai" / "figma" / "_probe.js").read_text(
                encoding="utf-8"
            )
            return FakeCompleted(0, "{}", "")

        with tempfile.TemporaryDirectory() as temp:
            cwd = Path(temp)
            screenshot = cwd / "evidence" / "actual.png"
            figma_measure.measure(
                "http://x", spec, cwd=cwd, runner=fake_runner,
                node_path="/usr/bin/node",
                viewport={"width": 390, "height": 844, "deviceScaleFactor": 2},
                screenshot=screenshot,
            )
        self.assertEqual(captured["env"]["FIGMA_MEASURE_SCREENSHOT"], str(screenshot.resolve()))
        self.assertIn('"width": 390', captured["script"])
        self.assertIn("page.screenshot", captured["script"])

    def test_measure_reports_install_hint_when_node_missing(self) -> None:
        spec = make_spec([])

        def boom(name, windows_fallback=None):
            raise RuntimeError(f"Required executable not found: {name}")

        with tempfile.TemporaryDirectory() as temp:
            with patch.object(figma_measure, "require_executable", boom):
                actuals = figma_measure.measure("http://x", spec, cwd=Path(temp))
        self.assertIn("__probe_error__", actuals)
        self.assertIn("Install Node.js", actuals["__probe_error__"]["__error"])

    def test_measure_reports_install_hint_when_playwright_missing(self) -> None:
        spec = make_spec([])

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            return FakeCompleted(1, "", "Error: Cannot find module 'playwright'")

        with tempfile.TemporaryDirectory() as temp:
            actuals = figma_measure.measure(
                "http://x", spec, cwd=Path(temp),
                runner=fake_runner, node_path="/usr/bin/node",
            )
        err = actuals["__probe_error__"]["__error"]
        self.assertIn("playwright not found", err)
        self.assertIn("npm i -D playwright", err)


class MainTests(unittest.TestCase):
    def test_main_returns_2_when_stack_flutter(self) -> None:
        argv = ["--url", "http://x", "--spec", "s.json", "--out", "o.json", "--stack", "flutter"]
        self.assertEqual(figma_measure.main(argv), 2)

    def test_main_returns_2_when_spec_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            argv = ["--url", "http://x", "--spec", str(Path(temp) / "nope.json"), "--out", "o.json"]
            self.assertEqual(figma_measure.main(argv), 2)

    def test_main_returns_2_when_spec_has_no_probes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            spec_path = Path(temp) / "spec.json"
            spec_path.write_text(json.dumps({"source": {}}), encoding="utf-8")
            out = Path(temp) / "out.json"
            argv = ["--url", "http://x", "--spec", str(spec_path), "--out", str(out)]
            self.assertEqual(figma_measure.main(argv), 2)

    def test_main_returns_2_when_probes_are_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            spec_path = Path(temp) / "spec.json"
            spec_path.write_text(json.dumps(make_spec([])), encoding="utf-8")
            argv = ["--url", "http://x", "--spec", str(spec_path), "--out", str(Path(temp) / "o.json")]
            self.assertEqual(figma_measure.main(argv), 2)

    def test_main_writes_report_and_returns_0_when_converged(self) -> None:
        spec = make_spec([
            {"name": "t", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        with tempfile.TemporaryDirectory() as temp:
            cwd = Path(temp)
            spec_path = cwd / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            out = cwd / "delta.json"

            def fake_runner(cmd, *, cwd=None, env=None, capture=False):
                return FakeCompleted(0, json.dumps({"t": {"fontSize": 24}}), "")

            with patch.object(figma_measure, "measure",
                              return_value={"t": {"fontSize": 24}}), \
                 patch.object(figma_measure, "run_cmd", fake_runner), \
                 patch.object(figma_measure, "require_executable", return_value="/usr/bin/node"):
                rc = figma_measure.main([
                    "--url", "http://x", "--spec", str(spec_path),
                    "--out", str(out), "--cwd", str(cwd),
                ])
            self.assertEqual(rc, 0)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(report["converged"])
            self.assertEqual(report["summary"]["passed"], 1)


if __name__ == "__main__":
    unittest.main()
