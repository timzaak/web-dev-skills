from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from email.message import Message
from dataclasses import dataclass
from pathlib import Path
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


DEFAULT_VP = [{"name": "default", "probes": None}]
VIEWPORT = {"width": 1280, "height": 900, "deviceScaleFactor": 1}


def compute(spec: dict, actuals: dict, **kw) -> object:
    return figma_measure.compute_delta(spec, {"default": actuals}, DEFAULT_VP, **kw)


class ClassifyNumericTests(unittest.TestCase):
    def test_px_under_2_is_pass(self) -> None:
        status, delta, _ = figma_measure.classify_delta("fontSize", 24, 24 + 1)
        self.assertEqual(status, "PASS")
        self.assertAlmostEqual(delta, 1.0)

    def test_px_string_values_parsed(self) -> None:
        status, _, _ = figma_measure.classify_delta("rowGap", "16px", "14px")
        self.assertEqual(status, "WARN")  # delta 2.0 -> WARN (2 <= d < 4)

    def test_px_4_or_more_is_fail(self) -> None:
        status, delta, _ = figma_measure.classify_delta("width", 320, 325)
        self.assertEqual(status, "FAIL")
        self.assertAlmostEqual(delta, 5.0)

    def test_px_exactly_4_is_fail(self) -> None:
        status, _, _ = figma_measure.classify_delta("height", 48, 52)
        self.assertEqual(status, "FAIL")

    def test_px_exactly_2_is_warn(self) -> None:
        # delta == 2.0 falls in WARN band [2, 4)
        status, _, _ = figma_measure.classify_delta("paddingTop", 16, 18)
        self.assertEqual(status, "WARN")

    def test_unparseable_is_missing(self) -> None:
        status, delta, _ = figma_measure.classify_delta("fontSize", "auto", 16)
        self.assertEqual(status, "MISSING")
        self.assertIsNone(delta)


class ClassifyPositionTests(unittest.TestCase):
    def test_x_under_2_is_pass(self) -> None:
        status, delta, _ = figma_measure.classify_delta("x", 16, 17)
        self.assertEqual(status, "PASS")
        self.assertAlmostEqual(delta, 1.0)

    def test_y_offset_4_is_fail(self) -> None:
        status, delta, _ = figma_measure.classify_delta("y", 24, 29)
        self.assertEqual(status, "FAIL")
        self.assertAlmostEqual(delta, 5.0)


class ClassifyDurationTests(unittest.TestCase):
    def test_equal_ms_is_pass(self) -> None:
        status, _, _ = figma_measure.classify_delta("transitionDuration", "200ms", "200ms")
        self.assertEqual(status, "PASS")

    def test_seconds_normalized(self) -> None:
        status, _, _ = figma_measure.classify_delta("animationDuration", "0.2s", "200ms")
        self.assertEqual(status, "PASS")

    def test_50ms_or_more_is_fail(self) -> None:
        status, _, _ = figma_measure.classify_delta("transitionDuration", "200ms", "260ms")
        self.assertEqual(status, "FAIL")

    def test_under_50ms_delta_is_warn(self) -> None:
        status, _, _ = figma_measure.classify_delta("transitionDuration", "200ms", "230ms")
        self.assertEqual(status, "WARN")

    def test_delay_matches_duration_thresholds(self) -> None:
        status, _, _ = figma_measure.classify_delta("transitionDelay", "0.1s", "100ms")
        self.assertEqual(status, "PASS")
        status, _, _ = figma_measure.classify_delta("transitionDelay", "0ms", "80ms")
        self.assertEqual(status, "FAIL")

    def test_uniform_computed_list_collapses(self) -> None:
        status, _, _ = figma_measure.classify_delta(
            "transitionDuration", "200ms", "0.2s, 0.2s"
        )
        self.assertEqual(status, "PASS")

    def test_non_uniform_computed_list_is_missing(self) -> None:
        status, delta, _ = figma_measure.classify_delta(
            "transitionDuration", "200ms", "0.2s, 0.3s"
        )
        self.assertEqual(status, "MISSING")
        self.assertIsNone(delta)


class ClassifyTimingTests(unittest.TestCase):
    def test_keyword_matches_cubic_bezier(self) -> None:
        status, _, _ = figma_measure.classify_delta(
            "transitionTimingFunction",
            "ease-in-out",
            "cubic-bezier(0.42, 0, 0.58, 1)",
        )
        self.assertEqual(status, "PASS")

    def test_bezier_spacing_and_zeros_normalized(self) -> None:
        status, _, _ = figma_measure.classify_delta(
            "transitionTimingFunction",
            "cubic-bezier(.42,0,.58,1)",
            "cubic-bezier(0.42, 0, 0.58, 1)",
        )
        self.assertEqual(status, "PASS")

    def test_mismatch_is_fail(self) -> None:
        status, _, _ = figma_measure.classify_delta(
            "transitionTimingFunction",
            "ease-out",
            "cubic-bezier(0.42, 0, 0.58, 1)",
        )
        self.assertEqual(status, "FAIL")

    def test_unsupported_format_is_advisory_warn(self) -> None:
        status, _, note = figma_measure.classify_delta(
            "transitionTimingFunction",
            "linear(0 50%, 1 100%)",
            "linear(0 50%, 1 100%)",
        )
        self.assertEqual(status, "WARN")
        self.assertIn("unsupported timing function", note)

    def test_steps_default_term_normalized(self) -> None:
        status, _, _ = figma_measure.classify_delta(
            "animationTimingFunction", "steps(4)", "steps(4, end)"
        )
        self.assertEqual(status, "PASS")

    def test_uniform_timing_list_collapses(self) -> None:
        status, _, _ = figma_measure.classify_delta(
            "transitionTimingFunction",
            "ease-out",
            "cubic-bezier(0, 0, 0.58, 1), cubic-bezier(0, 0, 0.58, 1)",
        )
        self.assertEqual(status, "PASS")


class ClassifyTransitionPropertyTests(unittest.TestCase):
    def test_spacing_normalized(self) -> None:
        status, _, _ = figma_measure.classify_delta(
            "transitionProperty", "transform,opacity", "transform, opacity"
        )
        self.assertEqual(status, "PASS")

    def test_mismatch_is_fail(self) -> None:
        status, _, _ = figma_measure.classify_delta(
            "transitionProperty", "transform", "all"
        )
        self.assertEqual(status, "FAIL")

    def test_empty_is_missing(self) -> None:
        status, _, _ = figma_measure.classify_delta("transitionProperty", "transform", "")
        self.assertEqual(status, "MISSING")


class ClassifyColorTests(unittest.TestCase):
    def test_hex_match(self) -> None:
        status, _, _ = figma_measure.classify_delta("color", "#1d4ed8", "#1D4ED8")
        self.assertEqual(status, "PASS")

    def test_rgb_hex_equivalent(self) -> None:
        status, _, _ = figma_measure.classify_delta("backgroundColor", "#1d4ed8", "rgb(29, 78, 216)")
        self.assertEqual(status, "PASS")

    def test_mismatch_is_fail(self) -> None:
        status, _, _ = figma_measure.classify_delta("color", "#000000", "rgb(255, 255, 255)")
        self.assertEqual(status, "FAIL")

    def test_short_hex_matches_long_hex(self) -> None:
        status, _, _ = figma_measure.classify_delta("color", "#fff", "rgb(255 255 255)")
        self.assertEqual(status, "PASS")

    def test_alpha_difference_fails(self) -> None:
        status, _, _ = figma_measure.classify_delta(
            "backgroundColor", "#1d4ed833", "rgba(29, 78, 216, 1)",
        )
        self.assertEqual(status, "FAIL")

    def test_unsupported_color_format_is_advisory_warn(self) -> None:
        status, _, note = figma_measure.classify_delta(
            "background", "linear-gradient(90deg, #fff, #000)", "rgb(255, 255, 255)",
        )
        self.assertEqual(status, "WARN")
        self.assertIn("unsupported color format", note)

    def test_display_p3_actual_is_advisory_warn(self) -> None:
        status, _, _ = figma_measure.classify_delta(
            "color", "#1d4ed8", "color(display-p3 0.2 0.3 0.8)",
        )
        self.assertEqual(status, "WARN")


class ClassifyEnumTests(unittest.TestCase):
    def test_font_weight_match(self) -> None:
        status, _, _ = figma_measure.classify_delta("fontWeight", 600, "600")
        self.assertEqual(status, "PASS")

    def test_font_weight_mismatch(self) -> None:
        status, _, _ = figma_measure.classify_delta("fontWeight", 600, "500")
        self.assertEqual(status, "FAIL")


class ClassifyLineHeightTests(unittest.TestCase):
    def test_equal_px_is_pass(self) -> None:
        status, _, _ = figma_measure.classify_delta("lineHeight", "24px", "24px")
        self.assertEqual(status, "PASS")

    def test_normal_vs_explicit_is_warn(self) -> None:
        status, _, note = figma_measure.classify_delta("lineHeight", "24px", "normal")
        self.assertEqual(status, "WARN")
        self.assertIn("normal", note)

    def test_both_normal_is_pass(self) -> None:
        status, _, _ = figma_measure.classify_delta("lineHeight", "normal", "normal")
        self.assertEqual(status, "PASS")

    def test_explicit_mismatch_is_fail(self) -> None:
        status, _, _ = figma_measure.classify_delta("lineHeight", "24px", "32px")
        self.assertEqual(status, "FAIL")


class ExpandProbesTests(unittest.TestCase):
    def test_padding_expands_to_four_sides(self) -> None:
        expanded = figma_measure.expand_probes([
            {"name": "card", "selector": ".c", "expect": {"padding": 16}},
        ])
        self.assertEqual(
            set(expanded[0]["expect"]),
            {"paddingTop", "paddingRight", "paddingBottom", "paddingLeft"},
        )

    def test_gap_expands_to_row_and_column(self) -> None:
        expanded = figma_measure.expand_probes([
            {"name": "g", "selector": ".g", "expect": {"gap": 8}},
        ])
        self.assertEqual(set(expanded[0]["expect"]), {"rowGap", "columnGap"})

    def test_border_radius_expands_to_four_corners(self) -> None:
        expanded = figma_measure.expand_probes([
            {"name": "r", "selector": ".r", "expect": {"borderRadius": 12}},
        ])
        self.assertEqual(len(expanded[0]["expect"]), 4)

    def test_longhand_and_position_pass_through(self) -> None:
        expanded = figma_measure.expand_probes([
            {"name": "t", "selector": ".t", "expect": {"paddingTop": 8, "x": 16, "y": 24}},
        ])
        self.assertEqual(expanded[0]["expect"], {"paddingTop": 8, "x": 16, "y": 24})


class ComputeDeltaTests(unittest.TestCase):
    def test_converged_when_no_fail(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24, "fontWeight": 600}},
        ])
        report = compute(spec, {"title": {"fontSize": 24, "fontWeight": "600"}})
        self.assertTrue(report.converged)
        self.assertEqual(report.failed, 0)
        self.assertEqual(report.passed, 2)

    def test_not_converged_when_fail_present(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        report = compute(spec, {"title": {"fontSize": 30}})
        self.assertFalse(report.converged)
        self.assertEqual(report.failed, 1)

    def test_missing_probe_recorded(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        report = compute(spec, {})
        self.assertFalse(report.converged)
        self.assertEqual(report.missing, 1)

    def test_probe_error_recorded(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24, "color": "#000"}},
        ])
        report = compute(spec, {"title": {"__error": "element not found: .t"}})
        self.assertEqual(report.errored, 2)
        self.assertFalse(report.converged)

    def test_shorthand_expect_measures_every_side(self) -> None:
        spec = make_spec([
            {"name": "card", "selector": ".card", "expect": {"padding": 16}},
        ])
        # Right side is off by 8px: only a full four-side check catches it.
        report = compute(spec, {"card": {
            "paddingTop": 16, "paddingRight": 24, "paddingBottom": 16, "paddingLeft": 16,
        }})
        self.assertEqual(report.total, 4)
        self.assertEqual(report.failed, 1)
        self.assertFalse(report.converged)
        failed = [r for r in report.results if r.status == "FAIL"]
        self.assertEqual(failed[0].prop, "paddingRight")

    def test_gap_shorthand_checks_row_and_column(self) -> None:
        spec = make_spec([
            {"name": "row", "selector": ".row", "expect": {"gap": 16}},
        ])
        report = compute(spec, {"row": {"rowGap": 16, "columnGap": 18}})
        self.assertTrue(report.converged)
        self.assertEqual(report.warned, 1)

    def test_position_probe_classified(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"x": 16, "y": 24}},
        ])
        report = compute(spec, {"title": {"x": 16, "y": 40}})
        self.assertEqual(report.passed, 1)
        self.assertEqual(report.failed, 1)

    def test_declared_conflict_applies_to_shorthand_sides(self) -> None:
        spec = make_spec([
            {"name": "card", "selector": ".card", "expect": {"padding": 13}},
        ])
        conflicts = [{
            "name": "card", "prop": "padding", "spec": 13,
            "projectValue": 16, "token": "space-4", "reason": "existing token",
        }]
        report = compute(
            spec,
            {"card": {
                "paddingTop": 16, "paddingRight": 16, "paddingBottom": 16, "paddingLeft": 16,
            }},
            conflicts=conflicts,
        )
        self.assertTrue(report.converged)
        self.assertEqual(report.conflicted, 4)
        self.assertEqual(report.results[0].status, "CONFLICT")

    def test_conflict_does_not_hide_unexpected_actual_value(self) -> None:
        spec = make_spec([
            {"name": "card", "selector": ".card", "expect": {"padding": 13}},
        ])
        conflicts = [{
            "name": "card", "prop": "padding", "spec": 13,
            "projectValue": 16, "token": "space-4", "reason": "existing token",
        }]
        report = compute(
            spec,
            {"card": {
                "paddingTop": 20, "paddingRight": 20, "paddingBottom": 20, "paddingLeft": 20,
            }},
            conflicts=conflicts,
        )
        self.assertFalse(report.converged)
        self.assertEqual(report.failed, 4)
        self.assertEqual(report.results[0].status, "FAIL")

    def test_missing_element_is_counted_as_missing(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".title", "expect": {"fontSize": 24}},
        ])
        report = compute(spec, {"title": {"__missing": "element not found"}})
        self.assertEqual(report.missing, 1)
        self.assertEqual(report.errored, 0)

    def test_report_target_is_measured_url(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".title", "expect": {"fontSize": 24}},
        ])
        report = compute(
            spec, {"title": {"fontSize": 24}}, target_url="http://localhost/page",
        )
        self.assertEqual(report.target, "http://localhost/page")

    def test_meta_from_actuals_lands_in_report(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        report = compute(spec, {"title": {"fontSize": 24}, "__meta": {"networkidle": False}})
        self.assertEqual(report.meta.get("networkidle"), False)

    def test_integrity_from_spec_lands_in_meta(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        spec["integrity"] = {"metadataNodeCount": 12, "specNodeCount": 9}
        report = compute(spec, {"title": {"fontSize": 24}})
        self.assertEqual(report.meta["integrity"]["specNodeCount"], 9)

    def test_spec_revision_lands_in_meta(self) -> None:
        spec = make_spec([{"name": "a", "selector": ".a", "expect": {"fontSize": 12}}])
        spec["revision"] = 3
        report = compute(spec, {"a": {"fontSize": 12}})
        self.assertEqual(report.meta["specRevision"], 3)

    def test_coverage_ratio_computed_when_probeable_nodes_declared(self) -> None:
        spec = make_spec([
            {"name": "a", "selector": ".a", "expect": {"fontSize": 24}},
            {"name": "b", "selector": ".b", "expect": {"fontSize": 16}},
        ])
        spec["probeableNodes"] = 4
        report = compute(spec, {"a": {"fontSize": 24}, "b": {"fontSize": 16}})
        self.assertEqual(report.coverage["probes"], 2)
        self.assertEqual(report.coverage["probeableNodes"], 4)
        self.assertEqual(report.coverage["ratio"], 0.5)

    def test_coverage_null_without_probeable_nodes(self) -> None:
        spec = make_spec([
            {"name": "a", "selector": ".a", "expect": {"fontSize": 24}},
        ])
        report = compute(spec, {"a": {"fontSize": 24}})
        self.assertIsNone(report.coverage["probeableNodes"])
        self.assertIsNone(report.coverage["ratio"])

    def test_to_dict_shape(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        report = compute(spec, {"title": {"fontSize": 24}})
        d = report.to_dict()
        self.assertEqual(d["summary"]["total"], 1)
        self.assertEqual(d["results"][0]["name"], "title")
        for key in ("summary", "viewports", "coverage", "meta"):
            self.assertIn(key, d)


class ComputeDeltaViewportTests(unittest.TestCase):
    def test_multi_viewport_with_per_viewport_probes(self) -> None:
        mobile_probe = {"name": "t", "selector": ".t", "expect": {"fontSize": 16}}
        spec = make_spec([
            {"name": "t", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        spec["viewport"] = [
            {"name": "mobile", "width": 390, "height": 844, "deviceScaleFactor": 2,
             "probes": [mobile_probe]},
            {"name": "desktop", "width": 1280, "height": 900},
        ]
        report = figma_measure.compute_delta(
            spec,
            {"mobile": {"t": {"fontSize": 16}}, "desktop": {"t": {"fontSize": 24}}},
            [
                {"name": "mobile", "probes": [mobile_probe]},
                {"name": "desktop", "probes": None},
            ],
        )
        self.assertTrue(report.converged)
        self.assertEqual(report.passed, 2)
        self.assertEqual(report.viewports["mobile"]["total"], 1)
        self.assertEqual(report.viewports["desktop"]["total"], 1)
        self.assertEqual(report.results[0].viewport, "mobile")
        self.assertEqual(report.results[1].viewport, "desktop")

    def test_missing_viewport_actuals_block_convergence(self) -> None:
        spec = make_spec([
            {"name": "t", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        report = figma_measure.compute_delta(
            spec,
            {"desktop": {"t": {"fontSize": 24}}},
            [{"name": "mobile"}, {"name": "desktop"}],
        )
        self.assertFalse(report.converged)
        self.assertEqual(report.missing, 1)
        self.assertFalse(report.viewports["mobile"]["converged"])
        self.assertTrue(report.viewports["desktop"]["converged"])


class ResolveViewportsTests(unittest.TestCase):
    def test_dict_viewport_yields_single_entry(self) -> None:
        spec = {"viewport": {"width": 390, "height": 844, "deviceScaleFactor": 2}}
        entries = figma_measure.resolve_viewports(spec)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["name"], "390x844")
        self.assertEqual(entries[0]["width"], 390)

    def test_array_viewport_yields_named_entries(self) -> None:
        spec = {"viewport": [
            {"name": "mobile", "width": 390, "height": 844},
            {"width": 1280, "height": 900},
        ]}
        entries = figma_measure.resolve_viewports(spec)
        self.assertEqual([e["name"] for e in entries], ["mobile", "1280x900"])
        self.assertEqual(entries[0]["deviceScaleFactor"], 1.0)

    def test_array_entry_probes_carried_through(self) -> None:
        probes = [{"name": "t", "selector": ".t", "expect": {"fontSize": 16}}]
        spec = {"viewport": [{"name": "mobile", "width": 390, "height": 844, "probes": probes}]}
        entries = figma_measure.resolve_viewports(spec)
        self.assertEqual(entries[0]["probes"], probes)

    def test_cli_override_forces_single_viewport(self) -> None:
        spec = {"viewport": [
            {"name": "mobile", "width": 390, "height": 844},
            {"name": "desktop", "width": 1280, "height": 900},
        ]}
        entries = figma_measure.resolve_viewports(spec, width=800, height=600)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["width"], 800)
        self.assertIsNone(entries[0]["probes"])

    def test_missing_viewport_falls_back_to_root_layout_then_default(self) -> None:
        spec = {"nodes": [{"layout": {"width": 320, "height": 720}}]}
        entries = figma_measure.resolve_viewports(spec)
        self.assertEqual((entries[0]["width"], entries[0]["height"]), (320, 720))
        entries = figma_measure.resolve_viewports({})
        self.assertEqual((entries[0]["width"], entries[0]["height"]), (1280, 900))

    def test_invalid_entry_raises(self) -> None:
        spec = {"viewport": [{"width": 390}]}
        with self.assertRaises(ValueError):
            figma_measure.resolve_viewports(spec)

    def test_name_sanitized_for_filenames(self) -> None:
        spec = {"viewport": [{"name": "mobile / v2", "width": 390, "height": 844}]}
        entries = figma_measure.resolve_viewports(spec)
        self.assertEqual(entries[0]["name"], "mobile-v2")


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
            captured["env"] = env
            probe_file = Path(str(cwd)) / "memo" / "figma" / "_probe.js"
            captured["script"] = probe_file.read_text(encoding="utf-8")
            return FakeCompleted(0, json.dumps({"title": {"fontSize": 24}}), "")

        with tempfile.TemporaryDirectory() as temp:
            actuals = figma_measure.measure(
                "http://localhost:3000/x", spec, cwd=Path(temp),
                viewport=VIEWPORT, runner=fake_runner, node_path="/usr/bin/node",
            )
        self.assertEqual(actuals, {"title": {"fontSize": 24}})
        self.assertEqual(captured["env"]["FIGMA_MEASURE_URL"], "http://localhost:3000/x")
        self.assertIn("PATH", captured["env"])
        self.assertIn("require('playwright')", captured["script"])
        self.assertIn('"selector": ".t"', captured["script"])

    def test_measure_expands_shorthand_in_probe_script(self) -> None:
        spec = make_spec([
            {"name": "card", "selector": ".c", "expect": {"padding": 16, "x": 8}},
        ])
        captured = {}

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            probe_file = Path(str(cwd)) / "memo" / "figma" / "_probe.js"
            captured["script"] = probe_file.read_text(encoding="utf-8")
            return FakeCompleted(0, "{}", "")

        with tempfile.TemporaryDirectory() as temp:
            figma_measure.measure(
                "http://x", spec, cwd=Path(temp), viewport=VIEWPORT,
                runner=fake_runner, node_path="/usr/bin/node",
            )
        self.assertIn('"paddingTop"', captured["script"])
        self.assertIn('"x"', captured["script"])

    def test_measure_script_stabilizes_before_probing(self) -> None:
        spec = make_spec([
            {"name": "title", "selector": ".t", "expect": {"fontSize": 24}},
        ])
        captured = {}

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            probe_file = Path(str(cwd)) / "memo" / "figma" / "_probe.js"
            captured["script"] = probe_file.read_text(encoding="utf-8")
            return FakeCompleted(0, "{}", "")

        with tempfile.TemporaryDirectory() as temp:
            figma_measure.measure(
                "http://x", spec, cwd=Path(temp), viewport=VIEWPORT,
                runner=fake_runner, node_path="/usr/bin/node",
            )
        for marker in ("document.fonts.ready", "waitForSelector", "getAnimations", "networkidle"):
            self.assertIn(marker, captured["script"])

    def test_measure_returns_error_on_nonzero(self) -> None:
        spec = make_spec([])

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            return FakeCompleted(1, "", "boom")

        with tempfile.TemporaryDirectory() as temp:
            actuals = figma_measure.measure(
                "http://x", spec, cwd=Path(temp), viewport=VIEWPORT,
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
                "http://x", spec, cwd=Path(temp), viewport=VIEWPORT,
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
                "http://x", spec, cwd=cwd, viewport=VIEWPORT,
                runner=fake_runner, node_path="/usr/bin/node",
            )
            self.assertFalse((cwd / "memo" / "figma" / "_probe.js").exists())

    def test_measure_passes_viewport_and_screenshot_to_probe(self) -> None:
        spec = make_spec([])
        captured = {}

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            captured["env"] = env
            captured["script"] = (Path(cwd) / "memo" / "figma" / "_probe.js").read_text(
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

    def test_measure_passes_scope_selector_for_element_screenshot(self) -> None:
        spec = make_spec([])
        captured = {}

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            captured["env"] = env
            captured["script"] = (Path(cwd) / "memo" / "figma" / "_probe.js").read_text(encoding="utf-8")
            return FakeCompleted(0, "{}", "")

        with tempfile.TemporaryDirectory() as temp:
            figma_measure.measure(
                "http://x", spec, cwd=Path(temp), viewport=VIEWPORT,
                runner=fake_runner, node_path="node", screenshot=Path(temp) / "scope.png",
                scope_selector="[data-figma='hero']",
            )
        self.assertEqual(captured["env"]["FIGMA_MEASURE_SCOPE"], "[data-figma='hero']")
        self.assertIn("scope.screenshot", captured["script"])

    def test_measure_reports_install_hint_when_node_missing(self) -> None:
        spec = make_spec([])

        def boom(name, windows_fallback=None):
            raise RuntimeError(f"Required executable not found: {name}")

        with tempfile.TemporaryDirectory() as temp:
            with patch.object(figma_measure, "require_executable", boom):
                actuals = figma_measure.measure(
                    "http://x", spec, cwd=Path(temp), viewport=VIEWPORT,
                )
        self.assertIn("__probe_error__", actuals)
        self.assertIn("Install Node.js", actuals["__probe_error__"]["__error"])

    def test_measure_reports_install_hint_when_playwright_missing(self) -> None:
        spec = make_spec([])

        def fake_runner(cmd, *, cwd=None, env=None, capture=False):
            return FakeCompleted(1, "", "Error: Cannot find module 'playwright'")

        with tempfile.TemporaryDirectory() as temp:
            actuals = figma_measure.measure(
                "http://x", spec, cwd=Path(temp), viewport=VIEWPORT,
                runner=fake_runner, node_path="/usr/bin/node",
            )
        err = actuals["__probe_error__"]["__error"]
        self.assertIn("playwright not found", err)
        self.assertIn("npm i -D playwright", err)


class PixelDiffTests(unittest.TestCase):
    def test_missing_images_skip_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = figma_measure.pixel_diff(
                Path(temp) / "nope-baseline.png",
                Path(temp) / "nope-actual.png",
                Path(temp) / "diff.png",
            )
        self.assertIn("skipped", result)
        self.assertTrue(
            "pixelmatch" in result["skipped"] or "cannot read" in result["skipped"],
            result["skipped"],
        )


class MediaRangeTests(unittest.TestCase):
    class Response:
        def __init__(self, status: int, content_range: str) -> None:
            self.status = status
            self.headers = Message()
            self.headers["Content-Range"] = content_range

        def getcode(self):
            return self.status

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def test_video_range_passes_on_206(self) -> None:
        def opener(request, timeout=0):
            self.assertEqual(request.headers["Range"], "bytes=0-1")
            return self.Response(206, "bytes 0-1/100")

        result = figma_measure.check_media_ranges(
            "http://localhost/page", [{"kind": "video", "name": "hero", "publicUrl": "/assets/hero.mp4"}],
            opener=opener,
        )
        self.assertEqual(result[0]["status"], "PASS")

    def test_video_without_public_url_is_error(self) -> None:
        result = figma_measure.check_media_ranges("http://localhost/page", [{"kind": "video", "name": "hero"}])
        self.assertEqual(result[0]["status"], "ERROR")

    def test_images_are_ignored(self) -> None:
        self.assertEqual(figma_measure.check_media_ranges("http://localhost", [{"kind": "image"}]), [])


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

    def test_main_archives_iteration_and_stamps_report(self) -> None:
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
                    "--out", str(out), "--cwd", str(cwd), "--iteration", "2",
                ])
            self.assertEqual(rc, 0)
            archive = cwd / "iterations" / "iter-02.json"
            self.assertTrue(archive.is_file())
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["iteration"], 2)
            archived = json.loads(archive.read_text(encoding="utf-8"))
            self.assertEqual(archived["summary"]["passed"], 1)

    def test_main_pixel_diff_never_breaks_measurement(self) -> None:
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
                    "--out", str(out), "--cwd", str(cwd), "--pixel-diff",
                ])
            self.assertEqual(rc, 0)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(report["converged"])
            self.assertIsNotNone(report["pixelDiff"])
            self.assertIn("skipped", report["pixelDiff"])


if __name__ == "__main__":
    unittest.main()
