#!/usr/bin/env python3
"""Measure rendered UI against a Figma spec.json and emit a delta report.

Renders the target page via the host project's Playwright, probes declared
elements with getComputedStyle + getBoundingClientRect, then classifies each
probe against thresholds defined in
${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md.

Only depends on the Python standard library. Playwright is invoked through the
target project's `npx playwright` to avoid adding a plugin-level dependency.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from lib.cli import require_executable, run_cmd


# --- thresholds (mirror figma-restore-contract.md Delta Thresholds) ---------
NUMERIC_PASS_PX = 2.0
NUMERIC_WARN_PX = 4.0
DURATION_PASS_MS = 0.0
DURATION_WARN_MS = 50.0

NUMERIC_PROPS = {
    "fontSize", "width", "height", "padding", "margin", "gap", "borderRadius",
}
COLOR_PROPS = {"color", "background", "backgroundColor", "borderColor"}
DURATION_PROPS = {"transitionDuration", "animationDuration"}
ENUM_PROPS = {"fontWeight", "opacity", "lineHeight"}
SUPPORTED_PROPS = NUMERIC_PROPS | COLOR_PROPS | DURATION_PROPS | ENUM_PROPS


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


@dataclass
class DeltaReport:
    target: str
    converged: bool
    total: int = 0
    passed: int = 0
    warned: int = 0
    conflicted: int = 0
    failed: int = 0
    missing: int = 0
    errored: int = 0
    results: list[ProbeResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "converged": self.converged,
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "warned": self.warned,
                "conflicted": self.conflicted,
                "failed": self.failed,
                "missing": self.missing,
                "errored": self.errored,
            },
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


def _norm_color(value: Any) -> tuple[int, int, int, float] | str | None:
    """Normalize CSS hex/rgb/rgba colors to an RGBA tuple."""
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


def classify_delta(prop: str, spec_value: Any, actual_value: Any) -> tuple[str, float | None]:
    """Classify one probe property against contract thresholds.

    Returns (status, delta). delta is None for non-numeric / missing probes.
    Status is one of PASS / WARN / FAIL / MISSING.
    """
    if spec_value is None:
        return "MISSING", None
    if actual_value is None:
        return "MISSING", None

    if prop in NUMERIC_PROPS:
        spec = _parse_px(spec_value)
        actual = _parse_px(actual_value)
        if spec is None or actual is None:
            return "MISSING", None
        delta = abs(actual - spec)
        if delta < NUMERIC_PASS_PX:
            return "PASS", delta
        if delta < NUMERIC_WARN_PX:
            return "WARN", delta
        return "FAIL", delta

    if prop in DURATION_PROPS:
        spec = _parse_ms(spec_value)
        actual = _parse_ms(actual_value)
        if spec is None or actual is None:
            return "MISSING", None
        delta = abs(actual - spec)
        if delta <= DURATION_PASS_MS:
            return "PASS", delta
        if delta < DURATION_WARN_MS:
            return "WARN", delta
        return "FAIL", delta

    if prop in COLOR_PROPS:
        spec_color = _norm_color(spec_value)
        actual_color = _norm_color(actual_value)
        if spec_color is not None and spec_color == actual_color:
            return "PASS", 0.0
        return "FAIL", None

    if prop in ENUM_PROPS:
        if str(spec_value).strip() == str(actual_value).strip():
            return "PASS", 0.0
        return "FAIL", None

    # Unknown prop: exact-string compare, no delta.
    if str(spec_value).strip() == str(actual_value).strip():
        return "PASS", 0.0
    return "FAIL", None


def values_equal(prop: str, left: Any, right: Any) -> bool:
    """Compare two values exactly after property-aware normalization."""
    if prop in NUMERIC_PROPS:
        left_value, right_value = _parse_px(left), _parse_px(right)
        return left_value is not None and right_value is not None and left_value == right_value
    if prop in DURATION_PROPS:
        left_value, right_value = _parse_ms(left), _parse_ms(right)
        return left_value is not None and right_value is not None and left_value == right_value
    if prop in COLOR_PROPS:
        return _norm_color(left) is not None and _norm_color(left) == _norm_color(right)
    return str(left).strip() == str(right).strip()


def validate_probes(spec: dict[str, Any]) -> list[str]:
    """Return actionable validation errors for probeSelectors."""
    probes = spec.get("probeSelectors")
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
    actuals: dict[str, dict[str, Any]],
    *,
    target_url: str = "",
    conflicts: list[dict[str, Any]] | None = None,
) -> DeltaReport:
    """Compute a DeltaReport from spec.probeSelectors vs measured actuals.

    spec: parsed spec.json (must contain 'probeSelectors').
    actuals: { probeName: { prop: value } } from the browser probe.
    """
    target = target_url or str(spec.get("target", ""))
    report = DeltaReport(target=target, converged=False)
    conflict_map = {
        (item.get("name"), item.get("prop")): item
        for item in (conflicts or [])
        if isinstance(item, dict)
    }

    for probe in spec.get("probeSelectors", []):
        name = probe.get("name", "")
        selector = probe.get("selector", "")
        expect = probe.get("expect", {}) or {}
        measured = actuals.get(name)

        if measured is None:
            for prop, spec_val in expect.items():
                report.results.append(ProbeResult(
                    name=name, selector=selector, prop=prop,
                    spec=spec_val, actual=None, delta=None,
                    status="MISSING", note="probe not found in actuals",
                ))
                report.total += 1
                report.missing += 1
            continue

        if measured.get("__missing"):
            for prop, spec_val in expect.items():
                report.results.append(ProbeResult(
                    name=name, selector=selector, prop=prop,
                    spec=spec_val, actual=None, delta=None,
                    status="MISSING", note=str(measured.get("__missing")),
                ))
                report.total += 1
                report.missing += 1
            continue

        if measured.get("__error"):
            for prop, spec_val in expect.items():
                report.results.append(ProbeResult(
                    name=name, selector=selector, prop=prop,
                    spec=spec_val, actual=None, delta=None,
                    status="ERROR", note=str(measured.get("__error")),
                ))
                report.total += 1
                report.errored += 1
            continue

        for prop, spec_val in expect.items():
            actual_val = measured.get(prop)
            status, delta = classify_delta(prop, spec_val, actual_val)
            conflict = conflict_map.get((name, prop))
            if (
                status != "PASS"
                and conflict is not None
                and values_equal(prop, conflict.get("spec"), spec_val)
                and values_equal(prop, conflict.get("projectValue"), actual_val)
            ):
                status = "CONFLICT"
            report.results.append(ProbeResult(
                name=name, selector=selector, prop=prop,
                spec=spec_val, actual=actual_val, delta=delta, status=status,
            ))
            report.total += 1
            if status == "PASS":
                report.passed += 1
            elif status == "WARN":
                report.warned += 1
            elif status == "CONFLICT":
                report.conflicted += 1
            elif status == "FAIL":
                report.failed += 1
            elif status == "MISSING":
                report.missing += 1
            elif status == "ERROR":
                report.errored += 1

    report.converged = (
        report.failed == 0 and report.missing == 0 and report.errored == 0
    )
    return report


def resolve_viewport(
    spec: dict[str, Any],
    width: int | None = None,
    height: int | None = None,
    device_scale_factor: float | None = None,
) -> dict[str, int | float]:
    """Resolve viewport from CLI overrides, spec.viewport, then root layout."""
    declared = spec.get("viewport") if isinstance(spec.get("viewport"), dict) else {}
    nodes = spec.get("nodes") if isinstance(spec.get("nodes"), list) else []
    root_layout = nodes[0].get("layout", {}) if nodes and isinstance(nodes[0], dict) else {}
    resolved_width = (
        width if width is not None
        else declared.get("width") or root_layout.get("width") or 1280
    )
    resolved_height = (
        height if height is not None
        else declared.get("height") or root_layout.get("height") or 900
    )
    scale = (
        device_scale_factor if device_scale_factor is not None
        else declared.get("deviceScaleFactor") or 1
    )
    try:
        result = {
            "width": int(round(float(resolved_width))),
            "height": int(round(float(resolved_height))),
            "deviceScaleFactor": float(scale),
        }
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid viewport values: {exc}") from exc
    if result["width"] <= 0 or result["height"] <= 0 or result["deviceScaleFactor"] <= 0:
        raise ValueError("viewport width, height, and deviceScaleFactor must be positive")
    return result


def render_measurement_script(spec: dict[str, Any], viewport: dict[str, int | float]) -> str:
    """Render a self-contained Node script that drives Playwright and prints JSON.

    The script uses the target project's installed `playwright` (required as a
    peer); it boots chromium, navigates to --url, runs the probe, and prints the
    actuals object as JSON to stdout.
    """
    probes_json = json.dumps(spec.get("probeSelectors", []))
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
if (!URL) { console.error('FIGMA_MEASURE_URL env var required'); process.exit(2); }
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: VIEWPORT.width, height: VIEWPORT.height },
    deviceScaleFactor: VIEWPORT.deviceScaleFactor,
  });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
  const actuals = await page.evaluate((probes) => {
    const COLOR = new Set(['color','background','backgroundColor','borderColor']);
    const DURATION = new Set(['transitionDuration','animationDuration']);
    const out = {};
    for (const p of probes) {
      try {
        const el = document.querySelector(p.selector);
        if (!el) { out[p.name] = { __missing: 'element not found: ' + p.selector }; continue; }
        const cs = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        const values = {};
        for (const prop of Object.keys(p.expect || {})) {
          if (prop === 'width') values.width = rect.width;
          else if (prop === 'height') values.height = rect.height;
          else if (prop === 'padding') values.padding = parseFloat(cs.paddingTop);
          else if (prop === 'margin') values.margin = parseFloat(cs.marginTop);
          else if (prop === 'gap') values.gap = parseFloat(cs.gap);
          else if (prop === 'fontSize') values.fontSize = parseFloat(cs.fontSize);
          else if (prop === 'fontWeight') values.fontWeight = cs.fontWeight;
          else if (prop === 'lineHeight') values.lineHeight = cs.lineHeight;
          else if (prop === 'borderRadius') values.borderRadius = parseFloat(cs.borderTopLeftRadius);
          else if (COLOR.has(prop)) values[prop] = cs[prop === 'background' ? 'backgroundColor' : prop];
          else if (DURATION.has(prop)) values[prop] = cs[prop];
          else values[prop] = cs[prop];
        }
        out[p.name] = values;
      } catch (e) { out[p.name] = { __error: String(e) }; }
    }
    return out;
  }, PROBES);
  if (SCREENSHOT) await page.screenshot({ path: SCREENSHOT, fullPage: true });
  await browser.close();
  process.stdout.write(JSON.stringify(actuals));
})().catch((e) => { console.error(String(e)); process.exit(1); });
"""


def measure(
    url: str,
    spec: dict[str, Any],
    *,
    cwd: Path,
    runner: Any = None,
    node_path: str | None = None,
    viewport: dict[str, int | float] | None = None,
    screenshot: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Run the in-browser probe and return parsed actuals.

    The probe script is written under ``cwd/.ai/figma/_probe.js`` so Node can
    resolve the target project's installed ``playwright`` package.

    runner: injectable for tests; defaults to run_cmd.
    node_path: injectable for tests; defaults to require_executable('node').
    """
    runner = runner or run_cmd
    try:
        node = node_path or require_executable("node", windows_fallback="node.exe")
    except RuntimeError as exc:
        return {"__probe_error__": {
            "__error": f"{exc}. Install Node.js to run the measurement probe."
        }}
    script = render_measurement_script(spec, viewport or resolve_viewport(spec))
    env = os.environ.copy()
    env["FIGMA_MEASURE_URL"] = url
    if screenshot is not None:
        screenshot = screenshot.resolve()
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        env["FIGMA_MEASURE_SCREENSHOT"] = str(screenshot)
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
    parser.add_argument("--viewport-width", type=int, help="Override spec viewport width.")
    parser.add_argument("--viewport-height", type=int, help="Override spec viewport height.")
    parser.add_argument("--device-scale-factor", type=float, help="Override spec device scale factor.")
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

    probe_errors = validate_probes(spec)
    if probe_errors:
        print(f"invalid spec.json probes: {'; '.join(probe_errors)}", file=sys.stderr)
        return 2

    cwd = Path(args.cwd).resolve()
    try:
        viewport = resolve_viewport(
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
    actuals = measure(
        args.url, spec, cwd=cwd, viewport=viewport, screenshot=screenshot_path,
    )

    if "__probe_error__" in actuals:
        print(f"probe failed: {actuals['__probe_error__'].get('__error')}", file=sys.stderr)
        return 1

    report = compute_delta(spec, actuals, target_url=args.url, conflicts=conflicts)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = report.to_dict()["summary"]
    print(
        f"converged={report.converged} "
        f"pass={summary['passed']} warn={summary['warned']} conflict={summary['conflicted']} "
        f"fail={summary['failed']} missing={summary['missing']} "
        f"-> {out_path.as_posix()}",
        file=sys.stderr,
    )
    return 0 if report.converged else 1


if __name__ == "__main__":
    sys.exit(main())
