#!/usr/bin/env python3
"""Validate deterministic structure and cross-document design contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


STACKS = ("backend", "frontend", "flutter")
MAIN_HEADINGS = (
    "## 1. 需求概述",
    "## 2. 需求来源",
    "### 2.4 决策追踪",
    "### 2.5 设计覆盖矩阵",
    "## 3. 现有实现分析",
    "## 4. 总体方案",
    "### 4.2 交付端范围",
    "### 4.3 跨端契约",
    "## 6. 测试与验收策略",
    "## 7. 风险与验证动作",
    "## 8. 文件影响范围",
)
STACK_HEADINGS = {
    "backend": ("## 4. API 接口设计", "## 9. 详细设计", "## 12. 文件影响范围"),
    "frontend": ("## 4. 用户体验流", "### 5.3 页面结构 / 线框说明", "## 9. 详细设计", "## 11. 文件影响范围"),
    "flutter": ("## 4. 用户体验流", "### 6.1 API 依赖", "## 12. 详细设计", "## 14. 文件影响范围"),
}
PLACEHOLDERS = re.compile(
    r"\[(?:方案名称|feature|真实仓库路径|operationId|REQ/US-ID)\]"
)


@dataclass(frozen=True)
class Finding:
    code: str
    source: str
    message: str
    line: int | None = None


def line_number(text: str, needle: str) -> int | None:
    index = text.find(needle)
    return None if index < 0 else text.count("\n", 0, index) + 1


def section(text: str, heading_fragment: str) -> str:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if heading_fragment in line), None)
    if start is None:
        return ""
    level = len(lines[start]) - len(lines[start].lstrip("#"))
    end = len(lines)
    for i in range(start + 1, len(lines)):
        current = len(lines[i]) - len(lines[i].lstrip("#"))
        if current and current <= level and lines[i].startswith("#"):
            end = i
            break
    return "\n".join(lines[start:end])


def table_rows(text: str, heading_fragment: str) -> list[list[str]]:
    block = section(text, heading_fragment)
    rows: list[list[str]] = []
    for line in block.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows[1:] if rows else []


def clean_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def applicable_stacks(main_text: str) -> set[str]:
    result: set[str] = set()
    for cells in table_rows(main_text, "4.2 交付端范围"):
        if len(cells) < 3:
            continue
        stack = clean_cell(cells[0]).lower()
        status = clean_cell(cells[2])
        if stack in STACKS and status.startswith("适用") and not status.startswith("不适用"):
            result.add(stack)
    return result


def design_documents(main_path: Path) -> list[Path]:
    if not main_path.is_file():
        return []
    main_text = main_path.read_text(encoding="utf-8")
    paths = [main_path]
    design_dir = main_path.with_suffix("")
    for stack in STACKS:
        path = design_dir / f"{stack}.md"
        if stack in applicable_stacks(main_text) and path.is_file():
            paths.append(path)
    return paths


def design_fingerprint(main_path: Path) -> str | None:
    paths = design_documents(main_path)
    if not paths:
        return None
    digest = hashlib.sha256()
    for path in paths:
        role = "main" if path == main_path else path.stem
        digest.update(role.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def operation_map(text: str, heading: str) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for cells in table_rows(text, heading):
        if len(cells) < 3:
            continue
        operation = clean_cell(cells[0])
        method = clean_cell(cells[1]).upper()
        path = clean_cell(cells[2])
        if operation:
            result[operation] = (method, path)
    return result


def impact_rows(text: str) -> list[tuple[str, str]]:
    for fragment in ("8. 文件影响范围", "文件影响范围（后端文件）", "文件影响范围（前端文件）", "文件影响范围（Flutter 文件）"):
        rows = table_rows(text, fragment)
        if rows:
            return [(clean_cell(row[0]), clean_cell(row[1]).upper()) for row in rows if len(row) >= 2]
    return []


def validate_path(repo_root: Path, source: Path, rel_path: str, operation: str) -> list[Finding]:
    findings: list[Finding] = []
    if not rel_path or rel_path.startswith("[") or "..." in rel_path:
        return [Finding("INVALID_IMPACT_PATH", str(source), f"invalid impact path: {rel_path}")]
    candidate = (repo_root / rel_path).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return [Finding("IMPACT_PATH_OUTSIDE_REPO", str(source), rel_path)]
    if operation not in {"CREATE", "MODIFY", "DELETE"}:
        findings.append(Finding("INVALID_IMPACT_OPERATION", str(source), f"{rel_path}: {operation}"))
    elif operation == "CREATE":
        if not candidate.parent.exists():
            findings.append(Finding("CREATE_PARENT_MISSING", str(source), rel_path))
    elif not candidate.exists():
        findings.append(Finding("IMPACT_TARGET_MISSING", str(source), f"{operation}: {rel_path}"))
    return findings


def validate(main_path: Path, repo_root: Path, require_complete: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    if not main_path.is_file():
        return [Finding("DESIGN_DOC_MISSING", str(main_path), "main design document not found")]

    documents: dict[str, tuple[Path, str]] = {"main": (main_path, main_path.read_text(encoding="utf-8"))}
    main_text = documents["main"][1]
    design_dir = main_path.with_suffix("")
    state_path = design_dir / ".state.json"
    if require_complete and state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            findings.append(Finding("DESIGN_STATE_INVALID", str(state_path), str(exc)))
        else:
            if state.get("status") != "complete":
                findings.append(Finding("DESIGN_GENERATION_INCOMPLETE", str(state_path), str(state.get("status"))))
    for heading in MAIN_HEADINGS:
        if heading not in main_text:
            findings.append(Finding("MAIN_HEADING_MISSING", str(main_path), heading))

    stacks = applicable_stacks(main_text)
    if not table_rows(main_text, "4.2 交付端范围"):
        findings.append(Finding("DELIVERY_SCOPE_INVALID", str(main_path), "delivery scope table is empty"))

    for stack in stacks:
        path = design_dir / f"{stack}.md"
        if not path.is_file():
            findings.append(Finding("STACK_DOC_MISSING", str(path), f"{stack} is applicable"))
            continue
        text = path.read_text(encoding="utf-8")
        documents[stack] = (path, text)
        for heading in STACK_HEADINGS[stack]:
            if heading not in text:
                findings.append(Finding("STACK_HEADING_MISSING", str(path), heading))

    for path, text in documents.values():
        for match in PLACEHOLDERS.finditer(text):
            findings.append(
                Finding("TEMPLATE_PLACEHOLDER", str(path), match.group(0), line_number(text, match.group(0)))
            )

    coverage = table_rows(main_text, "2.5 设计覆盖矩阵")
    if not coverage:
        findings.append(Finding("COVERAGE_MATRIX_EMPTY", str(main_path), "add at least one trace row"))
    for row in coverage:
        if len(row) < 5 or any(not clean_cell(cell) for cell in row[:5]):
            findings.append(Finding("COVERAGE_ROW_INCOMPLETE", str(main_path), " | ".join(row)))

    backend_ops: dict[str, tuple[str, str]] = {}
    if "backend" in documents:
        backend_ops = operation_map(documents["backend"][1], "4.1 接口清单")
        if not backend_ops:
            findings.append(Finding("BACKEND_CONTRACT_EMPTY", str(documents["backend"][0]), "API operation table is empty"))
        main_ops = operation_map(main_text, "4.3 跨端契约")
        if main_ops != backend_ops:
            findings.append(Finding("MAIN_CONTRACT_MISMATCH", str(main_path), "operation/method/path differ from backend.md"))

    for stack in ("frontend", "flutter"):
        if stack not in documents or not backend_ops:
            continue
        dependencies = operation_map(documents[stack][1], "API 依赖")
        for operation, signature in dependencies.items():
            if operation not in backend_ops:
                findings.append(Finding("UNKNOWN_CONTRACT_OPERATION", str(documents[stack][0]), operation))
            elif backend_ops[operation] != signature:
                findings.append(Finding("CONTRACT_SIGNATURE_MISMATCH", str(documents[stack][0]), operation))

    main_impacts = set(impact_rows(main_text))
    if not main_impacts:
        findings.append(Finding("MAIN_IMPACT_EMPTY", str(main_path), "file impact table is empty"))
    for stack, (path, text) in documents.items():
        impacts = impact_rows(text)
        if stack != "main":
            missing = set(impacts) - main_impacts
            for rel_path, operation in sorted(missing):
                findings.append(Finding("IMPACT_NOT_AGGREGATED", str(main_path), f"{stack}: {operation} {rel_path}"))
        for rel_path, operation in impacts:
            findings.extend(validate_path(repo_root, path, rel_path, operation))

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate generated technical design documents.")
    parser.add_argument("main_document", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    main_document = args.main_document.resolve()
    repo_root = args.repo_root.resolve()
    findings = validate(main_document, repo_root, args.require_complete)
    documents = []
    for path in design_documents(main_document):
        try:
            documents.append(path.resolve().relative_to(repo_root).as_posix())
        except ValueError:
            documents.append(str(path.resolve()))
    result = {
        "status": "failed" if findings else "passed",
        "design_fingerprint": design_fingerprint(main_document),
        "design_documents": documents,
        "finding_count": len(findings),
        "findings": [asdict(item) for item in findings],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            location = f":{item.line}" if item.line else ""
            print(f"{item.source}{location}: {item.code}: {item.message}")
    else:
        print("Design structure check passed.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
