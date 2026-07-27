#!/usr/bin/env python3
"""Find unresolved-decision language in completed workflow artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"待确认",
        r"待(?:用户|产品|业务|负责人)(?:确认|决定|选择|裁决)",
        r"需确认",
        r"需(?:用户|产品|业务|负责人)(?:确认|决定|选择|裁决)",
        r"待定",
        r"\bTBD\b",
        r"\bTBC\b",
        r"\bTODO\s*:?\s*decision\b",
        r"(?<!不)需要(?:用户|产品|业务|负责人).{0,12}(?:确认|决定|选择|裁决)",
        r"后续确认",
        r"暂定",
        r"(?:A\s*/\s*B|二选一).{0,8}(?:均可|待定|后续)",
        r"\b(?:pending|awaiting)\s+(?:user|product|business|owner)?\s*"
        r"(?:decision|confirmation|approval|choice)\b",
        r"\b(?:needs?|requires?)\s+(?:a\s+)?(?:user|product|business|owner)\s+"
        r"(?:decision|confirmation|approval|choice)\b",
        r"\bto\s+be\s+(?:decided|confirmed)\b",
        r"\bundecided\b",
    )
]


def read_text(path: str) -> tuple[str, str]:
    if path == "-":
        return "<stdin>", sys.stdin.read()
    artifact = Path(path)
    return str(artifact), artifact.read_text(encoding="utf-8")


def scan(source: str, content: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        matched = sorted({pattern.pattern for pattern in PATTERNS if pattern.search(line)})
        if matched:
            findings.append(
                {
                    "source": source,
                    "line": line_number,
                    "text": line.strip(),
                    "patterns": matched,
                }
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect language that may hide unresolved decisions."
    )
    parser.add_argument("artifacts", nargs="+", help="Markdown paths, or - for stdin")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    findings: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    for artifact in args.artifacts:
        try:
            source, content = read_text(artifact)
            findings.extend(scan(source, content))
        except (OSError, UnicodeError) as exc:
            errors.append({"source": artifact, "error": str(exc)})

    result = {
        "status": "blocked" if findings or errors else "closed",
        "finding_count": len(findings),
        "findings": findings,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for finding in findings:
            print(f"{finding['source']}:{finding['line']}: {finding['text']}")
        for error in errors:
            print(f"{error['source']}: {error['error']}", file=sys.stderr)
        if not findings and not errors:
            print("Decision closure scan passed.")

    return 1 if findings or errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
