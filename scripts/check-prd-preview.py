#!/usr/bin/env python3
"""Validate PRD HTML Preview files in a target project."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


REQUIRED_SECTIONS = [
    "Overview",
    "Scope",
    "Flow",
    "States",
    "Rules",
    "Acceptance",
    "Assumptions",
]

FORBIDDEN_PATTERNS = {
    "endpoint detail": re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/api\b", re.IGNORECASE),
    "database DDL": re.compile(r"\b(CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE)\b", re.IGNORECASE),
    "migration detail": re.compile(r"\bmigration\b|数据库表|建表|迁移", re.IGNORECASE),
    "code type": re.compile(r"\b(pub\s+struct|interface\s+\w+|type\s+\w+\s*=)\b"),
    "schema detail": re.compile(r"请求参数表|响应字段表|HTTP\s*状态码|schema", re.IGNORECASE),
}

EXTERNAL_DEPENDENCY_PATTERNS = {
    "external script": re.compile(r"<script[^>]+src\s*=", re.IGNORECASE),
    "external stylesheet": re.compile(r"<link[^>]+rel=[\"']?stylesheet", re.IGNORECASE),
    "cdn reference": re.compile(r"https?://|//cdn\.|unpkg\.com|jsdelivr\.net", re.IGNORECASE),
    "module import": re.compile(r"\bimport\s+.*\s+from\s+[\"']", re.IGNORECASE),
}


@dataclass
class PreviewResult:
    prd: str
    preview: str
    ok: bool = True
    issues: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.ok = False
        self.issues.append(message)


def find_prd_files(root: Path, feature: str | None) -> list[Path]:
    prd_root = root / "docs" / "prd"
    if not prd_root.exists():
        return []

    files = [path for path in prd_root.rglob("*.md") if path.name != "00-index.md"]
    if feature and feature != "--all":
        normalized = feature.lower()
        files = [
            path
            for path in files
            if path.stem.lower() == normalized or normalized in path.stem.lower()
        ]
    return sorted(files)


def validate_preview(prd_path: Path, root: Path) -> PreviewResult:
    preview_path = prd_path.with_suffix(".html")
    result = PreviewResult(
        prd=str(prd_path.relative_to(root)),
        preview=str(preview_path.relative_to(root)),
    )

    if not preview_path.exists():
        result.fail("missing same-directory HTML Preview")
        return result

    html = preview_path.read_text(encoding="utf-8", errors="replace")
    source = str(prd_path.relative_to(root)).replace("\\", "/")

    if "<!doctype html" not in html.lower():
        result.fail("missing <!doctype html>")
    if "<style" not in html.lower():
        result.fail("missing inline CSS")
    if "data-prd-source" not in html:
        result.fail("missing data-prd-source")
    if source not in html.replace("\\", "/"):
        result.fail(f"missing source PRD path: {source}")

    for section in REQUIRED_SECTIONS:
        if section not in html:
            result.fail(f"missing required section: {section}")
        double_quote = f'data-prd-section="{section}"'
        single_quote = f"data-prd-section='{section}'"
        if double_quote not in html and single_quote not in html:
            result.fail(f"missing data-prd-section marker: {section}")

    for name, pattern in EXTERNAL_DEPENDENCY_PATTERNS.items():
        if pattern.search(html):
            result.fail(f"external dependency detected: {name}")

    for name, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(html):
            result.fail(f"forbidden content detected: {name}")

    has_example_data = re.search(r"示例|sample|example", html, re.IGNORECASE)
    if has_example_data and "示例数据，不是接口契约" not in html:
        result.fail("sample data appears without required disclaimer")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PRD HTML Preview files.")
    parser.add_argument("feature", nargs="?", default="--all", help="Feature name or --all")
    parser.add_argument("--root", default=".", help="Target project root, defaults to current directory")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    results = [validate_preview(path, root) for path in find_prd_files(root, args.feature)]
    summary = {
        "checked": len(results),
        "passed": sum(1 for item in results if item.ok),
        "failed": sum(1 for item in results if not item.ok),
        "results": [item.__dict__ for item in results],
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"PRD Preview check: {summary['passed']}/{summary['checked']} passed")
        for item in results:
            status = "PASS" if item.ok else "FAIL"
            print(f"[{status}] {item.preview}")
            for issue in item.issues:
                print(f"  - {issue}")

    return 0 if summary["failed"] == 0 and summary["checked"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
