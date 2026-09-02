#!/usr/bin/env python3
"""Measure rendered UI against a Figma spec.json and emit a delta report.

Renders the target page via the host project's Playwright, probes declared
elements with getComputedStyle + getBoundingClientRect, then classifies each
probe against thresholds defined in
${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md.

- shorthand expects (padding/margin/gap/borderRadius) expand to every
  side/corner; x/y positions are measured when declared;
- motion probes (duration/delay/timing function/transitionProperty)
  normalize keyword easings against their cubic-bezier equivalents and
  collapse uniform computed lists ("0.2s, 0.2s");
- the page is stabilized before probing (webfonts, frozen animations,
  probe attach wait); networkidle state lands in report meta;
- spec.viewport may be an array (responsive breakpoints) with optional
  per-viewport probe overrides;
- --pixel-diff adds an advisory pixel comparison (never affects
  convergence); --iteration archives each convergence round.

Python standard library only (pixelmatch/Pillow optional, for --pixel-diff).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from lib.cli import require_executable, run_cmd


# --- thresholds (mirror figma-workflow-contract.md Measurement) ------------
NUMERIC_PASS_PX = 2.0
NUMERIC_WARN_PX = 4.0
DURATION_PASS_MS = 0.0
DURATION_WARN_MS = 50.0
PIXEL_DIFF_ADVISORY_RATIO = 0.05

NUMERIC_PROPS = {
    "fontSize", "width", "height", "x", "y",
    "paddingTop", "paddingRight", "paddingBottom", "paddingLeft",
    "marginTop", "marginRight", "marginBottom", "marginLeft",
    "rowGap", "columnGap",
    "borderTopLeftRadius", "borderTopRightRadius",
    "borderBottomRightRadius", "borderBottomLeftRadius",
}
COLOR_PROPS = {"color", "background", "backgroundColor", "borderColor"}
DURATION_PROPS = {
    "transitionDuration", "animationDuration", "transitionDelay", "animationDelay",
}
TIMING_PROPS = {"transitionTimingFunction", "animationTimingFunction"}
ENUM_PROPS = {"fontWeight", "opacity", "lineHeight", "transitionProperty"}

# Shorthand expect keys expand to every longhand before measuring.
SHORTHAND_EXPANSION: dict[str, tuple[str, ...]] = {
    "padding": ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft"),
    "margin": ("marginTop", "marginRight", "marginBottom", "marginLeft"),
    "gap": ("rowGap", "columnGap"),
    "borderRadius": (
        "borderTopLeftRadius", "borderTopRightRadius",
        "borderBottomRightRadius", "borderBottomLeftRadius",
    ),
}
SHORTHAND_OF = {
    longhand: shorthand
    for shorthand, longhands in SHORTHAND_EXPANSION.items()
    for longhand in longhands
}
SUPPORTED_PROPS = (
    NUMERIC_PROPS | COLOR_PROPS | DURATION_PROPS | ENUM_PROPS | TIMING_PROPS
    | set(SHORTHAND_EXPANSION)
)


@dataclass
class ProbeResult:
    name: str
    selector: str
    prop: str
    spec: Any
    actual: Any
    delta: float | None
    status: str  # PASS | WARN | CONFLICT | FAIL | MISSING | ERROR
    note: str = ""
    viewport: str = "default"


@dataclass
class DeltaReport:
    target: str
    converged: bool
    iteration: int | None = None
    total: int = 0
    passed: int = 0
    warned: int = 0
    conflicted: int = 0
    failed: int = 0
    missing: int = 0
    errored: int = 0
    results: list[ProbeResult] = field(default_factory=list)
    viewports: dict[str, dict[str, Any]] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    coverage: dict[str, Any] = field(default_factory=dict)
    pixel_diff: dict[str, Any] | None = None
    media_ranges: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "converged": self.converged,
            "iteration": self.iteration,
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "warned": self.warned,
                "conflicted": self.conflicted,
                "failed": self.failed,
                "missing": self.missing,
                "errored": self.errored,
            },
            "viewports": self.viewports,
            "meta": self.meta,
            "coverage": self.coverage,
            "pixelDiff": self.pixel_diff,
            "mediaRanges": self.media_ranges,
            "results": [asdict(r) for r in self.results],
        }


def _parse_px(value: Any) -> float | None:
    """Extract a numeric pixel value from '16px' / 16 / '1rem'-like input."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text.endswith("px"):
        text = text[:-2]
    try:
        return float(text)
    except ValueError:
        return None


def _parse_ms(value: Any) -> float | None:
    """Extract milliseconds from '200ms' / 0.2s / 200."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    factor = 1.0
    if text.endswith("ms"):
        text = text[:-2]
    elif text.endswith("s"):
        text = text[:-1]
        factor = 1000.0
    try:
        return float(text) * factor
    except ValueError:
        return None


def _split_top_level(text: str) -> list[str]:
    """Split on commas outside parentheses (cubic-bezier/steps contain commas)."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    parts.append("".join(current).strip())
    return parts


def _collapse_uniform(value: Any, single: Any) -> Any:
    """Collapse computed multi-value lists ('0.2s, 0.2s') when entries are equal.

    Non-uniform lists and unparseable entries return None so callers can
    classify them instead of comparing raw strings.
    """
    text = str(value).strip()
    if "," not in text:
        return single(text)
    parts = [single(part) for part in _split_top_level(text)]
    if any(part is None for part in parts) or len(set(parts)) != 1:
        return None
    return parts[0]


def _format_timing_number(value: float) -> str:
    return f"{value:g}"


TIMING_KEYWORD_BEZIERS = {
    "linear": (0.0, 0.0, 1.0, 1.0),
    "ease": (0.25, 0.1, 0.25, 1.0),
    "ease-in": (0.42, 0.0, 1.0, 1.0),
    "ease-out": (0.0, 0.0, 0.58, 1.0),
    "ease-in-out": (0.42, 0.0, 0.58, 1.0),
}
TIMING_STEP_TERMS = (
    "jump-start", "jump-end", "jump-none", "jump-both", "start", "end",
)


def _norm_timing_single(text: str) -> str | None:
    """Normalize one CSS timing function to a canonical comparable string."""
    value = re.sub(r"\s+", "", text).lower()
    if value in TIMING_KEYWORD_BEZIERS:
        x1, y1, x2, y2 = TIMING_KEYWORD_BEZIERS[value]
        return "cubic-bezier({}, {}, {}, {})".format(
            _format_timing_number(x1), _format_timing_number(y1),
            _format_timing_number(x2), _format_timing_number(y2),
        )
    if value.startswith("cubic-bezier(") and value.endswith(")"):
        parts = value[len("cubic-bezier("):-1].split(",")
        if len(parts) != 4:
            return None
        try:
            x1, y1, x2, y2 = (float(part) for part in parts)
        except ValueError:
            return None
        return "cubic-bezier({}, {}, {}, {})".format(
            _format_timing_number(x1), _format_timing_number(y1),
            _format_timing_number(x2), _format_timing_number(y2),
        )
    if value.startswith("steps(") and value.endswith(")"):
        parts = value[len("steps("):-1].split(",")
        if len(parts) not in {1, 2} or not parts[0].isdigit():
            return None
        term = parts[1] if len(parts) == 2 else "end"
        if term not in TIMING_STEP_TERMS:
            return None
        return f"steps({parts[0]},{term})"
    return None


def norm_timing(value: Any) -> str | None:
    """Normalize a (possibly comma-list) timing function; None if unsupported."""
    if value is None:
        return None
    return _collapse_uniform(value, _norm_timing_single)


def _norm_transition_property(value: Any) -> str | None:
    """Normalize transitionProperty to 'a, b' form; None if unparseable."""
    if value is None:
        return None
    parts = _split_top_level(str(value).strip())
    if not parts or any(not part for part in parts):
        return None
    return ", ".join(parts)


def _norm_color(value: Any) -> tuple[int, int, int, float] | str | None:
    """Normalize CSS hex/rgb/rgba colors to an RGBA tuple.

    Returns the lowercased text for values outside sRGB hex/rgb syntax
    (gradients, color(display-p3 ...), etc.) so callers can tell
    "unparseable" apart from "parsed".
    """
    if value is None:
        return None
    text = str(value).strip().lower()
    if text == "transparent":
        return 0, 0, 0, 0.0
    if text.startswith("#"):
        value_text = text[1:]
        if len(value_text) in {3, 4}:
            value_text = "".join(char * 2 for char in value_text)
        if len(value_text) in {6, 8} and re.fullmatch(r"[0-9a-f]+", value_text):
            red, green, blue = (int(value_text[index:index + 2], 16) for index in (0, 2, 4))
            alpha = int(value_text[6:8], 16) / 255 if len(value_text) == 8 else 1.0
            return red, green, blue, round(alpha, 6)
    match = re.fullmatch(r"rgba?\((.*)\)", text)
    if match:
        body = match.group(1).replace(",", " ").replace("/", " / ")
        parts = body.split()
        try:
            slash = parts.index("/") if "/" in parts else -1
            color_parts = parts[:slash] if slash >= 0 else parts[:3]
            alpha_part = parts[slash + 1] if slash >= 0 else (parts[3] if len(parts) > 3 else "1")
            if len(color_parts) != 3:
                return text or None

            def channel(part: str) -> int:
                number = float(part[:-1]) * 2.55 if part.endswith("%") else float(part)
                return max(0, min(255, round(number)))

            alpha = float(alpha_part[:-1]) / 100 if alpha_part.endswith("%") else float(alpha_part)
            return (*[channel(part) for part in color_parts], round(max(0.0, min(1.0, alpha)), 6))
        except (ValueError, IndexError):
            return text or None
    return text or None


def classify_delta(prop: str, spec_value: Any, actual_value: Any) -> tuple[str, float | None, str]:
    """Classify one probe property against contract thresholds.

    Returns (status, delta, note); delta is None for non-numeric probes.
    note explains advisory cases (lineHeight 'normal', unsupported colors).
    """
    if spec_value is None or actual_value is None:
        return "MISSING", None, ""

    if prop in NUMERIC_PROPS:
        spec = _parse_px(spec_value)
        actual = _parse_px(actual_value)
        if spec is None or actual is None:
            return "MISSING", None, ""
        delta = abs(actual - spec)
        if delta < NUMERIC_PASS_PX:
            return "PASS", delta, ""
        if delta < NUMERIC_WARN_PX:
            return "WARN", delta, ""
        return "FAIL", delta, ""

    if prop in DURATION_PROPS:
        spec = _collapse_uniform(spec_value, _parse_ms)
        actual = _collapse_uniform(actual_value, _parse_ms)
        if spec is None or actual is None:
            return "MISSING", None, ""
        delta = abs(actual - spec)
        if delta <= DURATION_PASS_MS:
            return "PASS", delta, ""
        if delta < DURATION_WARN_MS:
            return "WARN", delta, ""
        return "FAIL", delta, ""

    if prop in COLOR_PROPS:
        spec_color = _norm_color(spec_value)
        actual_color = _norm_color(actual_value)
        if isinstance(spec_color, str) or isinstance(actual_color, str):
            return (
                "WARN", None,
                "unsupported color format (gradient / color(display-p3) / color-mix); "
                "needs human review",
            )
        if spec_color is not None and spec_color == actual_color:
            return "PASS", 0.0, ""
        return "FAIL", None, ""

    if prop == "lineHeight":
        spec_text = str(spec_value).strip()
        actual_text = str(actual_value).strip()
        if spec_text == actual_text:
            return "PASS", 0.0, ""
        if "normal" in (spec_text, actual_text):
            return (
                "WARN", None,
                "lineHeight 'normal' vs explicit value; align spec or set explicit line-height",
            )
        return "FAIL", None, ""

    if prop in TIMING_PROPS:
        spec_fn = norm_timing(spec_value)
        actual_fn = norm_timing(actual_value)
        if spec_fn is None or actual_fn is None:
            return (
                "WARN", None,
                "unsupported timing function format (spring / linear()); "
                "needs human review",
            )
        if spec_fn == actual_fn:
            return "PASS", 0.0, ""
        return "FAIL", None, ""

    if prop == "transitionProperty":
        spec_prop = _norm_transition_property(spec_value)
        actual_prop = _norm_transition_property(actual_value)
        if spec_prop is None or actual_prop is None:
            return "MISSING", None, ""
        if spec_prop == actual_prop:
            return "PASS", 0.0, ""
        return "FAIL", None, ""

    if prop in ENUM_PROPS:
        if str(spec_value).strip() == str(actual_value).strip():
            return "PASS", 0.0, ""
        return "FAIL", None, ""

    # Unknown prop: exact-string compare, no delta.
    if str(spec_value).strip() == str(actual_value).strip():
        return "PASS", 0.0, ""
    return "FAIL", None, ""


def values_equal(prop: str, left: Any, right: Any) -> bool:
    """Compare two values exactly after property-aware normalization."""
    if prop in NUMERIC_PROPS:
        left_value, right_value = _parse_px(left), _parse_px(right)
        return left_value is not None and right_value is not None and left_value == right_value
    if prop in DURATION_PROPS:
        left_value = _collapse_uniform(left, _parse_ms)
        right_value = _collapse_uniform(right, _parse_ms)
        return left_value is not None and right_value is not None and left_value == right_value
    if prop in TIMING_PROPS:
        return norm_timing(left) is not None and norm_timing(left) == norm_timing(right)
    if prop == "transitionProperty":
        left_value = _norm_transition_property(left)
        return (
            left_value is not None
            and left_value == _norm_transition_property(right)
        )
    if prop in COLOR_PROPS:
        return _norm_color(left) is not None and _norm_color(left) == _norm_color(right)
    return str(left).strip() == str(right).strip()


def expand_expect(expect: dict[str, Any] | None) -> dict[str, Any]:
    """Expand shorthand expect keys to their longhand equivalents."""
    expanded: dict[str, Any] = {}
    for prop, value in (expect or {}).items():
        if prop in SHORTHAND_EXPANSION:
            for longhand in SHORTHAND_EXPANSION[prop]:
                expanded[longhand] = value
        else:
            expanded[prop] = value
    return expanded


def expand_probes(probes: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Return probes with shorthand expects expanded for measurement."""
    return [{**probe, "expect": expand_expect(probe.get("expect"))} for probe in probes or []]


def validate_probes(probes: Any) -> list[str]:
    """Return actionable validation errors for a probeSelectors list."""
    if not isinstance(probes, list) or not probes:
        return ["probeSelectors must be a non-empty array"]
    errors: list[str] = []
    names: set[str] = set()
    for index, probe in enumerate(probes):
        if not isinstance(probe, dict):
            errors.append(f"probeSelectors[{index}] must be an object")
            continue
        name = probe.get("name")
        selector = probe.get("selector")
        expect = probe.get("expect")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"probeSelectors[{index}].name must be non-empty")
        elif name in names:
            errors.append(f"duplicate probe name: {name}")
        else:
            names.add(name)
        if not isinstance(selector, str) or not selector.strip():
            errors.append(f"probeSelectors[{index}].selector must be non-empty")
        if not isinstance(expect, dict) or not expect:
            errors.append(f"probeSelectors[{index}].expect must be a non-empty object")
        else:
            unknown = sorted(set(expect) - SUPPORTED_PROPS)
            if unknown:
                errors.append(f"probeSelectors[{index}] has unsupported properties: {', '.join(unknown)}")
    return errors


def validate_conflicts(conflicts: Any, spec: dict[str, Any]) -> list[str]:
    """Validate conflict evidence and ensure every item targets a real probe property."""
    if not isinstance(conflicts, list):
        return ["root must be an array"]
    probe_values = {
        (probe.get("name"), prop): value
        for probe in spec.get("probeSelectors", [])
        if isinstance(probe, dict)
        for prop, value in (probe.get("expect") or {}).items()
    }
    errors: list[str] = []
    keys: set[tuple[Any, Any]] = set()
    for index, item in enumerate(conflicts):
        if not isinstance(item, dict):
            errors.append(f"conflicts[{index}] must be an object")
            continue
        key = (item.get("name"), item.get("prop"))
        if key in keys:
            errors.append(f"duplicate conflict: {key[0]}.{key[1]}")
        keys.add(key)
        if key not in probe_values:
            errors.append(f"conflicts[{index}] does not match a probe property")
            continue
        for required in ("spec", "projectValue", "token", "reason"):
            if required not in item or item[required] in (None, ""):
                errors.append(f"conflicts[{index}].{required} is required")
        if "spec" in item and not values_equal(str(key[1]), item["spec"], probe_values[key]):
            errors.append(f"conflicts[{index}].spec does not match spec.json")
    return errors


def compute_delta(
    spec: dict[str, Any],
    actuals_by_vp: dict[str, dict[str, Any]],
    viewports: list[dict[str, Any]],
    *,
    target_url: str = "",
    conflicts: list[dict[str, Any]] | None = None,
) -> DeltaReport:
    """Compute a DeltaReport from spec.probeSelectors vs measured actuals.

    actuals_by_vp: ``{ viewportName: { probeName: { prop: value } } }``.
    viewports: ``[{ name, probes }]`` entries; probes=None falls back to
    spec.probeSelectors. Names must match the actuals map.
    """
    target = target_url or str(spec.get("target", ""))
    report = DeltaReport(target=target, converged=False)
    conflict_map = {
        (item.get("name"), item.get("prop")): item
        for item in (conflicts or [])
        if isinstance(item, dict)
    }

    for entry in viewports:
        vp_name = entry.get("name") or "default"
        vp_summary = report.viewports.setdefault(vp_name, {
            "total": 0, "passed": 0, "warned": 0, "conflicted": 0,
            "failed": 0, "missing": 0, "errored": 0,
        })
        measured_vp = actuals_by_vp.get(vp_name, {})
        if not isinstance(measured_vp, dict):
            measured_vp = {}
        vp_meta = measured_vp.get("__meta")
        if isinstance(vp_meta, dict):
            report.meta.update(vp_meta)

        for probe in entry.get("probes") or spec.get("probeSelectors", []):
            name = probe.get("name", "")
            selector = probe.get("selector", "")
            expect = expand_expect(probe.get("expect"))
            measured = measured_vp.get(name)

            if measured is None or measured.get("__missing") or measured.get("__error"):
                status = "MISSING" if measured is None or measured.get("__missing") else "ERROR"
                note = (
                    "probe not found in actuals" if measured is None
                    else str(measured.get("__missing") or measured.get("__error"))
                )
                for prop, spec_val in expect.items():
                    _record(report, vp_summary, ProbeResult(
                        name=name, selector=selector, prop=prop,
                        spec=spec_val, actual=None, delta=None,
                        status=status, note=note, viewport=vp_name,
                    ))
                continue

            for prop, spec_val in expect.items():
                actual_val = measured.get(prop)
                status, delta, note = classify_delta(prop, spec_val, actual_val)
                conflict = None
                for candidate in ((name, prop), (name, SHORTHAND_OF.get(prop))):
                    if candidate in conflict_map:
                        conflict = conflict_map[candidate]
                        break
                if (
                    status != "PASS"
                    and conflict is not None
                    and values_equal(prop, conflict.get("spec"), spec_val)
                    and values_equal(prop, conflict.get("projectValue"), actual_val)
                ):
                    status = "CONFLICT"
                _record(report, vp_summary, ProbeResult(
                    name=name, selector=selector, prop=prop,
                    spec=spec_val, actual=actual_val, delta=delta,
                    status=status, note=note, viewport=vp_name,
                ))

    for vp_summary in report.viewports.values():
        vp_summary["converged"] = (
            vp_summary["failed"] == 0
            and vp_summary["missing"] == 0
            and vp_summary["errored"] == 0
        )
    report.converged = (
        report.failed == 0 and report.missing == 0 and report.errored == 0
    )

    probeable = spec.get("probeableNodes")
    probe_count = len(spec.get("probeSelectors") or [])
    report.coverage = {
        "probes": probe_count,
        "probeableNodes": probeable if isinstance(probeable, int) else None,
        "ratio": (
            round(probe_count / probeable, 4)
            if isinstance(probeable, int) and probeable > 0
            else None
        ),
    }
    integrity = spec.get("integrity")
    if isinstance(integrity, dict):
        report.meta["integrity"] = integrity
    if isinstance(spec.get("revision"), int):
        report.meta["specRevision"] = spec["revision"]
    return report


def _record(report: DeltaReport, vp_summary: dict[str, Any], result: ProbeResult) -> None:
    report.results.append(result)
    report.total += 1
    vp_summary["total"] += 1
    attr = {
        "PASS": "passed", "WARN": "warned", "CONFLICT": "conflicted",
        "FAIL": "failed", "MISSING": "missing", "ERROR": "errored",
    }.get(result.status)
    if attr:
        setattr(report, attr, getattr(report, attr) + 1)
        vp_summary[attr] += 1


def _viewport_name(name: Any) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(name).strip())
    return cleaned or "default"


def _viewport_entry(
    width: Any, height: Any, scale: Any, probes: Any, name: Any = None,
) -> dict[str, Any]:
    try:
        vp_width = int(round(float(width)))
        vp_height = int(round(float(height)))
        vp_scale = float(scale)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid viewport values: {exc}") from exc
    if vp_width <= 0 or vp_height <= 0 or vp_scale <= 0:
        raise ValueError("viewport width, height, and deviceScaleFactor must be positive")
    return {
        "name": _viewport_name(name or f"{vp_width}x{vp_height}"),
        "width": vp_width,
        "height": vp_height,
        "deviceScaleFactor": vp_scale,
        "probes": probes,
    }


def resolve_viewports(
    spec: dict[str, Any],
    width: int | None = None,
    height: int | None = None,
    device_scale_factor: float | None = None,
) -> list[dict[str, Any]]:
    """Resolve measurement viewports: ``{ name, width, height, deviceScaleFactor, probes }``.

    CLI overrides force a single viewport. spec.viewport may be an object
    (single) or an array (responsive breakpoints, each optionally carrying
    its own probe overrides); missing values fall back to the root node
    layout, then 1280x900.
    """
    if width is not None or height is not None or device_scale_factor is not None:
        declared = spec.get("viewport") if isinstance(spec.get("viewport"), dict) else {}
        nodes = spec.get("nodes") if isinstance(spec.get("nodes"), list) else []
        root_layout = nodes[0].get("layout", {}) if nodes and isinstance(nodes[0], dict) else {}
        return [_viewport_entry(
            width if width is not None else declared.get("width") or root_layout.get("width") or 1280,
            height if height is not None else declared.get("height") or root_layout.get("height") or 900,
            device_scale_factor if device_scale_factor is not None else declared.get("deviceScaleFactor") or 1,
            None,
        )]

    declared = spec.get("viewport")
    if isinstance(declared, list) and declared:
        return [
            _viewport_entry(
                item.get("width"), item.get("height"),
                item.get("deviceScaleFactor", 1), item.get("probes"),
                name=item.get("name"),
            )
            for item in declared
        ]

    declared = declared if isinstance(declared, dict) else {}
    nodes = spec.get("nodes") if isinstance(spec.get("nodes"), list) else []
    root_layout = nodes[0].get("layout", {}) if nodes and isinstance(nodes[0], dict) else {}
    return [_viewport_entry(
        declared.get("width") or root_layout.get("width") or 1280,
        declared.get("height") or root_layout.get("height") or 900,
        declared.get("deviceScaleFactor") or 1,
        None,
    )]


def render_measurement_script(
    viewport: dict[str, int | float],
    probes: list[dict[str, Any]],
) -> str:
    """Render a self-contained Node script that drives Playwright and prints JSON."""
    probes_json = json.dumps(expand_probes(probes), ensure_ascii=False)
    return (
        PROBE_JS_TEMPLATE_WITH_BOOT
        .replace("__PROBES_JSON__", probes_json)
        .replace("__VIEWPORT_JSON__", json.dumps(viewport))
    )


PROBE_JS_TEMPLATE_WITH_BOOT = r"""const { chromium } = require('playwright');
const PROBES = __PROBES_JSON__;
const VIEWPORT = __VIEWPORT_JSON__;
const URL = process.env.FIGMA_MEASURE_URL;
const SCREENSHOT = process.env.FIGMA_MEASURE_SCREENSHOT;
const SCOPE = process.env.FIGMA_MEASURE_SCOPE;
if (!URL) { console.error('FIGMA_MEASURE_URL env var required'); process.exit(2); }
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: VIEWPORT.width, height: VIEWPORT.height },
    deviceScaleFactor: VIEWPORT.deviceScaleFactor,
  });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  const networkidle = await page.waitForLoadState('networkidle', { timeout: 5000 })
    .then(() => true).catch(() => false);
  await page.evaluate(() => Promise.race([
    document.fonts.ready,
    new Promise((resolve) => setTimeout(resolve, 5000)),
  ]));
  await Promise.all(PROBES.map((p) =>
    page.waitForSelector(p.selector, { state: 'attached', timeout: 3000 }).catch(() => null)));
  const actuals = await page.evaluate(async (probes) => {
    const RECT_PROPS = new Set(['width', 'height', 'x', 'y']);
    // Freeze animations/transitions so probes read the settled state; the
    // freeze keeps declared duration values readable for duration probes.
    try {
      const style = document.createElement('style');
      style.id = '__figma_measure_freeze__';
      style.textContent = '*{transition-property:none!important;animation-name:none!important;caret-color:transparent!important}';
      document.documentElement.appendChild(style);
      for (const anim of document.getAnimations()) {
        try {
          const infinite = anim.effect && anim.effect.getTiming
            && anim.effect.getTiming().iterations === Infinity;
          if (infinite) anim.cancel(); else if (anim.finish) anim.finish();
        } catch (e) { /* best effort */ }
      }
      await new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)));
    } catch (e) { /* best effort */ }
    const out = {};
    for (const p of probes) {
      try {
        const el = document.querySelector(p.selector);
        if (!el) { out[p.name] = { __missing: 'element not found: ' + p.selector }; continue; }
        const cs = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        const values = {};
        for (const prop of Object.keys(p.expect || {})) {
          if (RECT_PROPS.has(prop)) values[prop] = rect[prop];
          else if (prop === 'background') values[prop] = cs.backgroundColor;
          // gap 'normal' behaves as zero spacing; normalize for numeric delta.
          else if (prop === 'rowGap' || prop === 'columnGap') {
            const v = cs[prop];
            values[prop] = v === 'normal' ? '0px' : v;
          }
          else values[prop] = cs[prop];
        }
        out[p.name] = values;
      } catch (e) { out[p.name] = { __error: String(e) }; }
    }
    return out;
  }, PROBES);
  actuals.__meta = { networkidle };
  if (SCREENSHOT) {
    if (SCOPE) {
      const scope = page.locator(SCOPE).first();
      await scope.waitFor({ state: 'visible', timeout: 3000 });
      await scope.screenshot({ path: SCREENSHOT });
    } else {
      await page.screenshot({ path: SCREENSHOT, fullPage: true });
    }
  }
  await browser.close();
  process.stdout.write(JSON.stringify(actuals));
})().catch((e) => { console.error(String(e)); process.exit(1); });
"""


def measure(
    url: str,
    spec: dict[str, Any],
    *,
    cwd: Path,
    viewport: dict[str, int | float],
    probes: list[dict[str, Any]] | None = None,
    runner: Any = None,
    node_path: str | None = None,
    screenshot: Path | None = None,
    scope_selector: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Run the in-browser probe and return parsed actuals.

    The probe script is written under ``cwd/.ai/figma/_probe.js`` so Node can
    resolve the target project's installed ``playwright`` package.

    runner: injectable for tests; defaults to run_cmd.
    node_path: injectable for tests; defaults to require_executable('node').
    probes: optional probe override (per-viewport probes); defaults to
    spec.probeSelectors.
    """
    runner = runner or run_cmd
    try:
        node = node_path or require_executable("node", windows_fallback="node.exe")
    except RuntimeError as exc:
        return {"__probe_error__": {
            "__error": f"{exc}. Install Node.js to run the measurement probe."
        }}
    script = render_measurement_script(
        viewport, probes if probes is not None else spec.get("probeSelectors", []),
    )
    env = os.environ.copy()
    env["FIGMA_MEASURE_URL"] = url
    if screenshot is not None:
        screenshot = screenshot.resolve()
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        env["FIGMA_MEASURE_SCREENSHOT"] = str(screenshot)
    if scope_selector:
        env["FIGMA_MEASURE_SCOPE"] = scope_selector
    probe_file = cwd / ".ai" / "figma" / "_probe.js"
    probe_file.parent.mkdir(parents=True, exist_ok=True)
    probe_file.write_text(script, encoding="utf-8")
    try:
        result = runner(
            [node, probe_file.as_posix()],
            cwd=cwd, env=env, capture=True,
        )
    finally:
        try:
            probe_file.unlink(missing_ok=True)
        except OSError:
            pass

    if result.returncode != 0:
        stderr = result.stderr.strip()
        # Surface a clearer hint when playwright is not resolvable in cwd.
        if "Cannot find module 'playwright'" in stderr:
            stderr = (
                f"playwright not found in {cwd}. "
                f"Install it (npm i -D playwright && npx playwright install chromium) "
                f"or pass --cwd pointing at a directory whose node_modules has playwright.\n"
                f"Original: {stderr}"
            )
        return {"__probe_error__": {"__error": stderr or "probe failed"}}
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"__probe_error__": {"__error": f"invalid JSON from probe: {exc}"}}
    return parsed


def pixel_diff(baseline: Path, actual: Path, diff_out: Path) -> dict[str, Any]:
    """Advisory pixel diff of baseline vs actual via pixelmatch.

    Never raises: missing dependencies or unreadable images return a
    ``skipped`` entry. Resizes the actual image to the baseline dimensions
    when they differ, one more reason the result stays advisory-only.
    """
    try:
        from PIL import Image
        from pixelmatch.contrib.PIL import pixelmatch
    except ImportError as exc:
        return {
            "skipped": (
                "pixelmatch/Pillow not installed "
                f"({exc}); pip install pixelmatch Pillow"
            ),
        }
    try:
        base = Image.open(baseline).convert("RGBA")
        shot = Image.open(actual).convert("RGBA")
    except (OSError, ValueError) as exc:
        return {"skipped": f"cannot read baseline/actual image: {exc}"}
    resized = False
    if shot.size != base.size:
        shot = shot.resize(base.size, Image.Resampling.LANCZOS)
        resized = True
    mask = Image.new("RGBA", base.size)
    diff_pixels = pixelmatch(base, shot, mask, threshold=0.1)
    total = base.size[0] * base.size[1]
    ratio = (diff_pixels / total) if total else 0.0
    try:
        diff_out.parent.mkdir(parents=True, exist_ok=True)
        mask.save(diff_out)
        diff_image = str(diff_out)
    except OSError:
        diff_image = None
    return {
        "baseline": str(baseline),
        "actual": str(actual),
        "diffImage": diff_image,
        "diffPixels": diff_pixels,
        "totalPixels": total,
        "diffRatio": round(ratio, 6),
        "resized": resized,
        "advisory": ratio >= PIXEL_DIFF_ADVISORY_RATIO,
    }


def check_media_ranges(
    target_url: str,
    manifest: list[dict[str, Any]],
    *,
    opener: Any = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    """Verify that public video URLs support HTTP byte-range delivery."""
    results: list[dict[str, Any]] = []
    for asset in manifest:
        if not isinstance(asset, dict) or asset.get("kind") != "video":
            continue
        name = str(asset.get("name") or asset.get("id") or "video")
        public_url = asset.get("publicUrl")
        if not isinstance(public_url, str) or not public_url.strip():
            results.append({
                "name": name, "status": "ERROR",
                "reason": "video manifest entry requires publicUrl for Range verification",
            })
            continue
        url = urllib.parse.urljoin(target_url, public_url)
        request = urllib.request.Request(url, headers={"Range": "bytes=0-1"})
        try:
            with opener(request, timeout=10) as response:
                status = getattr(response, "status", response.getcode())
                content_range = response.headers.get("Content-Range", "")
            passed = status == 206 and content_range.lower().startswith("bytes 0-1/")
            results.append({
                "name": name, "url": url,
                "status": "PASS" if passed else "ERROR",
                "httpStatus": status, "contentRange": content_range,
                "reason": "" if passed else "server must return 206 and Content-Range for bytes=0-1",
            })
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            results.append({"name": name, "url": url, "status": "ERROR", "reason": str(exc)})
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure rendered UI against a Figma spec.json.",
    )
    parser.add_argument("--url", required=True, help="Target page URL (dev server must be running).")
    parser.add_argument("--spec", required=True, help="Path to spec.json.")
    parser.add_argument("--out", required=True, help="Path to write delta-report.json.")
    parser.add_argument("--cwd", default=".", help="Working dir with playwright installed (target project).")
    parser.add_argument("--conflicts", help="Path to conflicts.json; defaults beside spec.json when present.")
    parser.add_argument("--screenshot", help="Actual screenshot path; defaults to actual.png beside --out.")
    parser.add_argument("--viewport-width", type=int, help="Force a single viewport width (overrides spec).")
    parser.add_argument("--viewport-height", type=int, help="Force a single viewport height (overrides spec).")
    parser.add_argument("--device-scale-factor", type=float, help="Force device scale factor (overrides spec).")
    parser.add_argument("--iteration", type=int, help="Convergence iteration number; archives the report under iterations/ and stamps it.")
    parser.add_argument("--pixel-diff", action="store_true", help="Advisory pixel diff of baseline vs actual (requires pixelmatch + Pillow).")
    parser.add_argument("--baseline", help="Baseline image for --pixel-diff; defaults to baseline.png beside --spec.")
    parser.add_argument("--scope-selector", help="Crop screenshots to this DOM selector (for t-figma-fix).")
    parser.add_argument("--assets-manifest", help="Assets manifest; verifies HTTP Range for video publicUrl entries.")
    parser.add_argument("--stack", default="web", choices=["web", "flutter"],
                        help="Tech stack. Flutter is reserved and not implemented.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.stack != "web":
        print(f"stack '{args.stack}' is reserved and not implemented yet", file=sys.stderr)
        return 2

    spec_path = Path(args.spec)
    if not spec_path.is_file():
        print(f"spec not found: {spec_path}", file=sys.stderr)
        return 2

    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"invalid spec.json: {exc}", file=sys.stderr)
        return 2

    probe_errors = validate_probes(spec.get("probeSelectors"))
    if probe_errors:
        print(f"invalid spec.json probes: {'; '.join(probe_errors)}", file=sys.stderr)
        return 2

    cwd = Path(args.cwd).resolve()
    try:
        viewports = resolve_viewports(
            spec, args.viewport_width, args.viewport_height, args.device_scale_factor,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    conflicts_path = Path(args.conflicts) if args.conflicts else spec_path.with_name("conflicts.json")
    conflicts: list[dict[str, Any]] = []
    if conflicts_path.is_file():
        try:
            loaded_conflicts = json.loads(conflicts_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"invalid conflicts.json: {exc}", file=sys.stderr)
            return 2
        conflict_errors = validate_conflicts(loaded_conflicts, spec)
        if conflict_errors:
            print(f"invalid conflicts.json: {'; '.join(conflict_errors)}", file=sys.stderr)
            return 2
        conflicts = loaded_conflicts

    out_path = Path(args.out)
    screenshot_path = Path(args.screenshot) if args.screenshot else out_path.parent / "actual.png"

    actuals_by_vp: dict[str, dict[str, Any]] = {}
    for index, vp in enumerate(viewports):
        vp_errors = validate_probes(vp.get("probes") or spec.get("probeSelectors"))
        if vp_errors:
            print(
                f"invalid probes for viewport {vp['name']}: {'; '.join(vp_errors)}",
                file=sys.stderr,
            )
            return 2
        vp_screenshot = (
            screenshot_path if index == 0
            else out_path.parent / f"actual-{vp['name']}.png"
        )
        actuals = measure(
            args.url, spec, cwd=cwd,
            viewport={
                "width": vp["width"], "height": vp["height"],
                "deviceScaleFactor": vp["deviceScaleFactor"],
            },
            screenshot=vp_screenshot, probes=vp.get("probes"),
            scope_selector=args.scope_selector,
        )
        if "__probe_error__" in actuals:
            print(
                f"probe failed for viewport {vp['name']}: "
                f"{actuals['__probe_error__'].get('__error')}",
                file=sys.stderr,
            )
            return 1
        actuals_by_vp[vp["name"]] = actuals

    report = compute_delta(
        spec, actuals_by_vp,
        [{"name": vp["name"], "probes": vp.get("probes")} for vp in viewports],
        target_url=args.url, conflicts=conflicts,
    )
    if args.iteration is not None:
        report.iteration = args.iteration
    if args.pixel_diff:
        baseline = Path(args.baseline) if args.baseline else spec_path.with_name("baseline.png")
        report.pixel_diff = pixel_diff(
            baseline, screenshot_path, out_path.parent / "pixel-diff.png",
        )

    if args.assets_manifest:
        manifest_path = Path(args.assets_manifest)
        if not manifest_path.is_file():
            print(f"assets manifest not found: {manifest_path}", file=sys.stderr)
            return 2
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"invalid assets manifest: {exc}", file=sys.stderr)
            return 2
        if not isinstance(manifest, list):
            print("invalid assets manifest: root must be an array", file=sys.stderr)
            return 2
        report.media_ranges = check_media_ranges(args.url, manifest)
        if any(item.get("status") == "ERROR" for item in report.media_ranges):
            report.converged = False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
    out_path.write_text(payload, encoding="utf-8")
    if args.iteration is not None:
        archive = out_path.parent / "iterations" / f"iter-{args.iteration:02d}.json"
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_text(payload, encoding="utf-8")

    summary = report.to_dict()["summary"]
    print(
        f"converged={report.converged} "
        f"pass={summary['passed']} warn={summary['warned']} conflict={summary['conflicted']} "
        f"fail={summary['failed']} missing={summary['missing']} "
        f"viewports={','.join(report.viewports)} "
        f"-> {out_path.as_posix()}",
        file=sys.stderr,
    )
    if report.pixel_diff is not None:
        if "skipped" in report.pixel_diff:
            print(f"pixel diff skipped: {report.pixel_diff['skipped']}", file=sys.stderr)
        else:
            print(
                f"pixel diff advisory={report.pixel_diff['advisory']} "
                f"ratio={report.pixel_diff['diffRatio']}",
                file=sys.stderr,
            )
    return 0 if report.converged else 1


if __name__ == "__main__":
    sys.exit(main())
