#!/usr/bin/env python3
"""Containerized Trivy dependency CVE scan for a target project.

Stable contract (see skills/t-security-deps/SKILL.md): script filename, CLI
arguments, JSON output fields and exit codes. Docker image and cache dir are
project-overridable.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_IMAGE = "aquasec/trivy:0.68.1"
DEFAULT_SEVERITY = "HIGH,CRITICAL"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "t-tools" / "trivy"

SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "target", "dist", "build", ".ai", ".venv", "venv", "vendor", ".gradle", ".idea"}

MANIFEST_ECOSYSTEMS = {
    "package-lock.json": "npm",
    "npm-shrinkwrap.json": "npm",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm",
    "bun.lockb": "bun",
    "bun.lock": "bun",
    "Cargo.lock": "cargo",
    "pom.xml": "maven",
    "gradle.lockfile": "gradle",
    "go.sum": "go",
    "requirements.txt": "pip",
    "poetry.lock": "poetry",
    "Pipfile.lock": "pipenv",
    "composer.lock": "composer",
    "Gemfile.lock": "bundler",
    "packages.lock.json": "nuget",
}

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}


def _docker(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["MSYS_NO_PATHCONV"] = "1"
    return subprocess.run(
        ["docker", *args],
        text=True, encoding="utf-8", errors="replace", capture_output=capture, env=env,
    )


def docker_available() -> bool:
    return _docker(["version", "--format", "{{.Server.Version}}"], capture=True).returncode == 0


def find_manifests(target: Path) -> list[dict[str, str]]:
    manifests: list[dict[str, str]] = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            ecosystem = MANIFEST_ECOSYSTEMS.get(name)
            if ecosystem is None:
                continue
            relative = (Path(root) / name).relative_to(target).as_posix()
            manifests.append({"path": relative, "ecosystem": ecosystem})
    return sorted(manifests, key=lambda item: item["path"])


def run_trivy(image: str, cache_dir: Path, target: Path, severity: str) -> tuple[int, str, str]:
    """Run the pinned Trivy image against a read-only mount of target."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    result = _docker(
        [
            "run", "--rm",
            "-v", f"{cache_dir}:/root/.cache/",
            "-v", f"{target}:/data:ro",
            image,
            "fs", "--scanners", "vuln", "--format", "json", "--severity", severity, "--timeout", "15m", "/data",
        ],
        capture=True,
    )
    return result.returncode, result.stdout, result.stderr


def normalize(trivy_report: dict) -> list[dict]:
    vulnerabilities: list[dict] = []
    for result in trivy_report.get("Results") or []:
        manifest = result.get("Target", "")
        ecosystem = MANIFEST_ECOSYSTEMS.get(Path(manifest).name, "other")
        for item in result.get("Vulnerabilities") or []:
            vulnerabilities.append(
                {
                    "id": item.get("VulnerabilityID"),
                    "severity": item.get("Severity", "UNKNOWN"),
                    "package": item.get("PkgName"),
                    "installed": item.get("InstalledVersion"),
                    "fixed": item.get("FixedVersion") or None,
                    "ecosystem": ecosystem,
                    "manifest": manifest,
                    "url": item.get("PrimaryURL"),
                }
            )
    vulnerabilities.sort(
        key=lambda v: (SEVERITY_ORDER.get(v["severity"], 99), v["package"] or "", v["id"] or "")
    )
    return vulnerabilities


def run_scan(args: argparse.Namespace) -> int:
    findings: list[dict[str, str]] = []
    target = args.target.resolve()

    if not target.is_dir():
        result = _result("error", target, args, [], [], [finding("BAD_TARGET", f"target is not a directory: {args.target}")])
        _emit(result, args.json)
        return 1

    manifests = find_manifests(target)
    if not manifests:
        result = _result("error", target, args, [], [], [finding("NO_MANIFEST", "no scannable dependency manifest or lockfile under target")])
        _emit(result, args.json)
        return 1

    if not docker_available():
        result = _result("error", target, args, manifests, [], [finding("NO_DOCKER", "docker daemon is not available")])
        _emit(result, args.json)
        return 1

    code, stdout, stderr = run_trivy(args.image, args.cache_dir, target, args.severity)
    if code != 0:
        result = _result(
            "error", target, args, manifests, [],
            [finding("SCAN_FAILED", f"trivy exited {code}: {stderr.strip()[:500]}")],
        )
        _emit(result, args.json)
        return 1

    try:
        vulnerabilities = normalize(json.loads(stdout))
    except json.JSONDecodeError as exc:
        result = _result(
            "error", target, args, manifests, [],
            [finding("SCAN_FAILED", f"trivy output is not valid JSON: {exc}")],
        )
        _emit(result, args.json)
        return 1

    result = _result("passed", target, args, manifests, vulnerabilities, [])
    if vulnerabilities:
        result["status"] = "failed"
    _emit(result, args.json)
    return 2 if vulnerabilities else 0


def finding(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _result(
    status: str,
    target: Path,
    args: argparse.Namespace,
    manifests: list[dict[str, str]],
    vulnerabilities: list[dict],
    findings: list[dict[str, str]],
) -> dict:
    by_severity: dict[str, int] = {}
    for item in vulnerabilities:
        by_severity[item["severity"]] = by_severity.get(item["severity"], 0) + 1
    return {
        "status": status,
        "target": target.as_posix(),
        "image": args.image,
        "severity_filter": args.severity,
        "manifests": manifests,
        "vulnerability_count": len(vulnerabilities),
        "by_severity": dict(sorted(by_severity.items(), key=lambda kv: SEVERITY_ORDER.get(kv[0], 99))),
        "vulnerabilities": vulnerabilities,
        "finding_count": len(findings),
        "findings": findings,
    }


def _emit(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    for item in result["findings"]:
        print(f"ERROR {item['code']}: {item['message']}", file=sys.stderr)
    for item in result["vulnerabilities"]:
        fixed = item["fixed"] or "no fix"
        print(f"{item['severity']:<8} {item['id']:<20} {item['package']} {item['installed']} -> {fixed} [{item['ecosystem']}/{item['manifest']}]")
    if result["status"] == "passed":
        print(f"Security deps scan passed ({len(result['manifests'])} manifest(s), severity>={result['severity_filter']}).")
    elif result["status"] == "failed":
        print(f"Security deps scan failed: {result['vulnerability_count']} vulnerability(ies), severity>={result['severity_filter']}.")
    else:
        print("Security deps scan error.", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Containerized Trivy dependency CVE scan (Node / Rust / Java and other ecosystems).")
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan", help="scan a project directory for dependency CVEs")
    scan.add_argument("target", type=Path)
    scan.add_argument("--json", action="store_true")
    scan.add_argument("--severity", default=DEFAULT_SEVERITY)
    scan.add_argument("--image", default=DEFAULT_IMAGE)
    scan.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    scan.set_defaults(handler=run_scan)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
