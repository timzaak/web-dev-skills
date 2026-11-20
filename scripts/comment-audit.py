#!/usr/bin/env python
"""Pre-screen comments in uncommitted changes for /t-push arbitration.

Read-only. Emits a JSON candidate list; deletion decisions stay with the AI
per protocols/code-comment-contract.md.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from lib.cli import require_executable, run_cmd
from lib.paths import REPO_ROOT

SLASH_LINE_EXTS = {
    ".rs", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte",
    ".dart", ".kt", ".kts", ".swift", ".go", ".java", ".c", ".h", ".cpp",
    ".hpp", ".cc", ".cs", ".php",
}
HASH_LINE_EXTS = {".py", ".pyi", ".sh", ".bash", ".zsh", ".graphql", ".gql", ".rb", ".toml", ".yaml", ".yml"}
BLOCK_EXTS = {".css", ".scss", ".less"}
SOURCE_EXTS = SLASH_LINE_EXTS | HASH_LINE_EXTS | BLOCK_EXTS
MIN_DENSITY_COMMENTS = 3

WORKFLOW_REF = re.compile(r"\.ai/(?:design|task|user-stories)")
NARRATION = re.compile(
    r"(?:\bnow (?:uses?|handles?|calls?)\b|\bpreviously\b|\bchanged from\b"
    r"|\bmoved (?:from|to)\b|\brenam(?:e|ed)\b|\bprevious (?:approach|version|implementation)\b"
    r"|\bas requested\b|\bper (?:discussion|design doc|task)\b"
    r"|\bnewly (?:added|created|introduced)\b"
    r"|新增|改为|改用|原先|原来的|重构后|本次(?:变更|修改|新增)|不再使用|暂时|临时)",
    re.IGNORECASE,
)
BANNER = re.compile(r"(?:[-=]{4,}|#{4,}|~{3,})")
KEEP_LICENSE = re.compile(r"\b(?:copyright|spdx|@?license)\b", re.IGNORECASE)
KEEP_LINT = re.compile(
    r"(?:eslint-disable|stylelint-disable|@ts-ignore|@ts-expect-error|prettier-ignore"
    r"|rustfmt::skip|noinspection|noqa|pragma once|coverage:|cspell:)",
    re.IGNORECASE,
)
KEEP_TODO = re.compile(r"\b(?:TODO|FIXME)\b")
KEEP_TRACE = re.compile(r"\bUS[-_]?\d+\b|\buser[- ]?stor(?:y|ies)\b", re.IGNORECASE)
HUNK_NEW = re.compile(r"\+(\d+)(?:,\d+)? @@")


def git(*args: str, capture: bool = False):
    git_bin = require_executable("git")
    return run_cmd([git_bin, *args], cwd=REPO_ROOT, capture=capture)


def ensure_success(result, message: str) -> None:
    if result.returncode != 0:
        raise RuntimeError(message)


def split_z_output(text: str) -> list[str]:
    return [item for item in text.split("\0") if item]


def changed_files() -> tuple[list[str], set[str]]:
    tracked = git("diff", "--name-only", "-z", "HEAD", capture=True)
    ensure_success(tracked, "Unable to inspect tracked git changes.")
    untracked = git("ls-files", "--others", "--exclude-standard", "-z", capture=True)
    ensure_success(untracked, "Unable to inspect untracked git files.")
    tracked_paths = split_z_output(tracked.stdout)
    untracked_paths = set(split_z_output(untracked.stdout))
    files = sorted(set(tracked_paths) | untracked_paths)
    return [path.replace("\\", "/") for path in files], untracked_paths


def added_lines_from_diff(path: str) -> dict[int, str]:
    result = git("diff", "-U0", "HEAD", "--", path, capture=True)
    ensure_success(result, f"Unable to diff: {path}")
    added: dict[int, str] = {}
    new_start = 0
    in_hunk = False
    for line in result.stdout.splitlines():
        if line.startswith("@@"):
            match = HUNK_NEW.search(line)
            new_start = int(match.group(1)) if match else 0
            in_hunk = True
        elif in_hunk and line.startswith("+") and not line.startswith("+++"):
            added[new_start] = line[1:]
            new_start += 1
    return added


def read_file_lines(path: str) -> list[str]:
    target = REPO_ROOT / path
    if not target.is_file():
        return []
    return target.read_text(encoding="utf-8", errors="replace").splitlines()


def comment_kind(ext: str, line: str) -> str | None:
    stripped = line.lstrip()
    if ext in SLASH_LINE_EXTS:
        if stripped.startswith(("///", "//!")):
            return "doc"
        if stripped.startswith("//"):
            return "line"
    elif ext in HASH_LINE_EXTS:
        if stripped.startswith("#"):
            return "line"
    elif ext in BLOCK_EXTS:
        if stripped.startswith("/**"):
            return "doc"
        if stripped.startswith("/*") or stripped.startswith("*"):
            return "block"
    if ext == ".py" and stripped.startswith(('"""', "'''")):
        return "doc"
    return None


def comment_text(kind: str, line: str) -> str:
    stripped = line.lstrip()
    if kind == "line":
        return stripped.lstrip("/#").strip()
    if kind in {"doc", "block"}:
        return stripped.lstrip("/*").rstrip("*/").lstrip("*").strip()
    return stripped


def prohibition_signal(text: str) -> str | None:
    if WORKFLOW_REF.search(text):
        return "workflow-ref"
    if NARRATION.search(text):
        return "change-narration"
    if BANNER.search(text):
        return "section-banner"
    return None


def keep_marker(text: str, line_no: int) -> str | None:
    if line_no <= 10 and KEEP_LICENSE.search(text):
        return "license-header"
    if KEEP_LINT.search(text):
        return "lint-directive"
    if KEEP_TRACE.search(text):
        return "traceability"
    if KEEP_TODO.search(text):
        return "todo"
    return None


def classify(text: str, kind: str, line_no: int) -> tuple[str, list[str]]:
    workflow = WORKFLOW_REF.search(text)
    keep = keep_marker(text, line_no)
    if keep and not workflow:
        return "likely-keep", [keep]
    prohibition = prohibition_signal(text)
    if prohibition:
        return "remove-candidate", [prohibition]
    if kind == "doc":
        return "doc-comment", []
    return "plain", []


def audit(density_threshold: float) -> dict:
    files, untracked = changed_files()
    findings: list[dict] = []
    density_report: list[dict] = []
    added_comment_total = 0

    for path in files:
        ext = Path(path).suffix.lower()
        if ext not in SOURCE_EXTS:
            continue
        disk_lines = read_file_lines(path)
        if not disk_lines and path not in untracked:
            continue
        if path in untracked:
            added = {i + 1: text for i, text in enumerate(disk_lines)}
        else:
            added = added_lines_from_diff(path)
        existing = {i + 1: text for i, text in enumerate(disk_lines) if (i + 1) not in added}

        added_kinds: dict[int, str] = {}
        added_code = 0
        for line_no, text in added.items():
            kind = comment_kind(ext, text)
            if kind:
                added_kinds[line_no] = kind
            elif text.strip():
                added_code += 1

        added_comment_total += len(added_kinds)
        pending_review: list[dict] = []
        for line_no, text in sorted(added.items()):
            kind = added_kinds.get(line_no)
            if not kind:
                continue
            body = comment_text(kind, text)
            category, signals = classify(body, kind, line_no)
            if category == "plain":
                pending_review.append(
                    {"file": path, "line": line_no, "text": body, "scope": "added",
                     "category": "review-candidate", "signals": ["comment-density"]}
                )
            else:
                findings.append(
                    {"file": path, "line": line_no, "text": body, "scope": "added",
                     "category": category, "signals": signals}
                )

        comments = len(added_kinds)
        ratio = round(comments / added_code, 2) if added_code else (1.0 if comments else 0.0)
        flagged = comments >= MIN_DENSITY_COMMENTS and ratio >= density_threshold
        if comments:
            density_report.append(
                {"file": path, "added_comments": comments, "added_code": added_code,
                 "ratio": ratio, "flagged": flagged}
            )
        if flagged:
            findings.extend(pending_review)

        for line_no, text in sorted(existing.items()):
            kind = comment_kind(ext, text)
            if not kind:
                continue
            body = comment_text(kind, text)
            signal = prohibition_signal(body)
            if signal:
                findings.append(
                    {"file": path, "line": line_no, "text": body, "scope": "existing",
                     "category": "remove-candidate", "signals": [signal]}
                )

    remove_candidates = sum(1 for f in findings if f["category"] == "remove-candidate")
    existing_violations = sum(1 for f in findings if f["scope"] == "existing")
    return {
        "summary": {
            "changed_source_files": len(density_report),
            "added_comment_lines": added_comment_total,
            "remove_candidates": remove_candidates,
            "existing_violations": existing_violations,
            "density_flagged_files": sum(1 for d in density_report if d["flagged"]),
        },
        "findings": findings,
        "density": density_report,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--density-threshold", type=float, default=0.2,
                        help="Flag files whose added-comment/added-code ratio reaches this value.")
    args = parser.parse_args(argv)
    try:
        report = audit(args.density_threshold)
    except RuntimeError as error:
        print(f"comment-audit: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
