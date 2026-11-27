#!/usr/bin/env python3
"""Verify t-anchor comments in published docs against target code content hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ANCHOR_LINE = re.compile(
    r"^<!--\s*t-anchor:\s*id=(?P<id>[A-Za-z0-9][A-Za-z0-9_-]*)"
    r"\s*\|\s*(?P<path>[^\s|]+):(?P<start>\d+)-(?P<end>\d+)"
    r"\s*\|\s*sha256=(?P<digest>[0-9a-f]{64})\s*-->$"
)

@dataclass(frozen=True)
class Finding:
    code: str
    source: str
    message: str
    line: int | None = None


@dataclass(frozen=True)
class AnchorResult:
    id: str
    source: str
    line: int
    target: str
    start: int
    end: int
    status: str


def normalized_lines(text: str) -> list[str]:
    unified = text.replace("\r\n", "\n").replace("\r", "\n")
    return [line.rstrip(" \t") for line in unified.split("\n")]


def content_hash(lines: list[str]) -> str:
    payload = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_lines(path: Path) -> list[str]:
    with open(path, encoding="utf-8", newline="") as handle:
        return normalized_lines(handle.read())


def target_within_root(root: Path, raw: str) -> Path | None:
    if "\\" in raw or Path(raw).is_absolute() or raw.startswith("/"):
        return None
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def find_content(lines: list[str], digest: str, width: int, skip_start: int) -> int | None:
    for index in range(0, len(lines) - width + 1):
        if index == skip_start:
            continue
        if content_hash(lines[index : index + width]) == digest:
            return index + 1
    return None


def verify_document(doc_path: Path, source: str, root: Path) -> tuple[list[AnchorResult], list[Finding]]:
    anchors: list[AnchorResult] = []
    findings: list[Finding] = []
    seen_ids: dict[str, int] = {}

    for number, raw_line in enumerate(read_lines(doc_path), start=1):
        line = raw_line.strip()
        if "t-anchor" not in line:
            continue
        match = ANCHOR_LINE.fullmatch(line)
        if match is None:
            findings.append(
                Finding("INVALID_ANCHOR_SYNTAX", source, "line is not a valid t-anchor comment", number)
            )
            continue

        anchor_id = match.group("id")
        raw_path = match.group("path")
        start = int(match.group("start"))
        end = int(match.group("end"))
        digest = match.group("digest")

        if anchor_id in seen_ids:
            findings.append(
                Finding(
                    "DUPLICATE_ANCHOR_ID",
                    source,
                    f"id '{anchor_id}' already used at line {seen_ids[anchor_id]}",
                    number,
                )
            )
            continue
        seen_ids[anchor_id] = number

        target = target_within_root(root, raw_path)
        if target is None:
            findings.append(
                Finding("INVALID_TARGET_PATH", source, f"target path escapes project root: {raw_path}", number)
            )
            anchors.append(AnchorResult(anchor_id, source, number, raw_path, start, end, "invalid"))
            continue

        if not target.is_file():
            findings.append(
                Finding("MISSING_TARGET_FILE", source, f"target file does not exist: {raw_path}", number)
            )
            anchors.append(AnchorResult(anchor_id, source, number, raw_path, start, end, "missing-file"))
            continue

        try:
            lines = read_lines(target)
        except UnicodeDecodeError:
            findings.append(
                Finding("INVALID_TARGET_PATH", source, f"target file is not valid UTF-8 text: {raw_path}", number)
            )
            anchors.append(AnchorResult(anchor_id, source, number, raw_path, start, end, "invalid"))
            continue

        width = end - start + 1
        if start < 1 or end < start:
            findings.append(
                Finding("INVALID_ANCHOR_RANGE", source, f"invalid line range {start}-{end}", number)
            )
            anchors.append(AnchorResult(anchor_id, source, number, raw_path, start, end, "invalid"))
            continue

        if width <= len(lines) and content_hash(lines[start - 1 : end]) == digest:
            anchors.append(AnchorResult(anchor_id, source, number, raw_path, start, end, "ok"))
            continue

        moved_at = find_content(lines, digest, width, start - 1)
        if moved_at is not None:
            anchors.append(AnchorResult(anchor_id, source, number, raw_path, start, end, "moved"))
            continue

        findings.append(
            Finding(
                "ANCHOR_DRIFTED",
                source,
                f"target content no longer matches sha256 ({raw_path}:{start}-{end})",
                number,
            )
        )
        anchors.append(AnchorResult(anchor_id, source, number, raw_path, start, end, "drifted"))

    return anchors, findings


def build_anchor_line(root: Path, raw_path: str, start: int, end: int, anchor_id: str) -> str:
    target = target_within_root(root, raw_path)
    if target is None:
        raise ValueError(f"target path escapes project root: {raw_path}")
    if not target.is_file():
        raise ValueError(f"target file does not exist: {raw_path}")
    lines = read_lines(target)
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"line range {start}-{end} outside {raw_path} ({len(lines)} lines)")
    digest = content_hash(lines[start - 1 : end])
    return f"<!-- t-anchor: id={anchor_id} | {raw_path}:{start}-{end} | sha256={digest} -->"


def display_source(doc_path: Path, root: Path) -> str:
    try:
        return doc_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(doc_path)


def run_verify(args: argparse.Namespace) -> int:
    findings: list[Finding] = []
    anchors: list[AnchorResult] = []
    root = args.project_root.resolve()

    for raw_doc in args.docs:
        doc_path = Path(raw_doc).resolve()
        source = display_source(doc_path, root)
        if not doc_path.is_file():
            findings.append(Finding("DOC_NOT_FOUND", source, "document does not exist"))
            continue
        doc_anchors, doc_findings = verify_document(doc_path, source, root)
        anchors.extend(doc_anchors)
        findings.extend(doc_findings)

    moved_count = sum(1 for anchor in anchors if anchor.status == "moved")
    result = {
        "status": "failed" if findings else "passed",
        "anchor_count": len(anchors),
        "moved_count": moved_count,
        "anchors": [asdict(anchor) for anchor in anchors],
        "finding_count": len(findings),
        "findings": [asdict(finding) for finding in findings],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for item in findings:
            location = f":{item.line}" if item.line else ""
            print(f"{item.source}{location}: {item.code}: {item.message}")
        if moved_count:
            print(f"{moved_count} anchor(s) moved (content found at a different position).")
        if not findings:
            print(f"Doc anchor check passed ({len(anchors)} anchor(s)).")
    return 1 if findings else 0


def run_print(args: argparse.Namespace) -> int:
    root = args.project_root.resolve()
    try:
        print(build_anchor_line(root, args.path, args.start, args.end, args.id))
    except (ValueError, UnicodeDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify t-anchor comments against target code content hashes.")
    commands = parser.add_subparsers(dest="command", required=True)

    verify = commands.add_parser("verify", help="verify anchor comments inside documents")
    verify.add_argument("docs", nargs="+", type=Path)
    verify.add_argument("--project-root", type=Path, default=Path.cwd())
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(handler=run_verify)

    emit = commands.add_parser("print", help="print a ready-to-paste anchor comment")
    emit.add_argument("path")
    emit.add_argument("start", type=int)
    emit.add_argument("end", type=int)
    emit.add_argument("--id", required=True)
    emit.add_argument("--project-root", type=Path, default=Path.cwd())
    emit.set_defaults(handler=run_print)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
