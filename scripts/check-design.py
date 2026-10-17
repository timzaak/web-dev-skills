#!/usr/bin/env python3
"""Validate deterministic structure and cross-document design contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


SKILL_ROOT_PREFIXES = (".claude/skills/", ".agents/skills/", "skills/")
MAIN_HEADINGS = (
    "## 1. 需求概述", "## 2. 需求来源", "### 2.4 决策追踪",
    "### 2.5 设计覆盖矩阵", "## 3. 现有实现分析", "## 4. 总体方案",
    "### 4.2 交付端范围", "### 4.3 跨端契约", "## 6. 测试与验收策略",
    "## 7. 风险与验证动作", "## 8. 文件影响范围",
)
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


def module_documents(main_path: Path) -> dict[str, Path]:
    text = main_path.read_text(encoding="utf-8")
    result: dict[str, Path] = {}
    design_dir = main_path.with_suffix("").resolve()
    for cells in table_rows(text, "4.2 交付端范围"):
        if len(cells) != 3:
            raise ValueError("Each scope row must contain module ID, document and status")
        module, document, status = (clean_cell(cell) for cell in cells)
        if status.startswith("不适用"):
            continue
        if not status.startswith("适用") or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", module):
            raise ValueError(f"Invalid scope row: {cells}")
        if module in result:
            raise ValueError(f"Duplicate module ID: {module}")
        if document == "main":
            path = main_path.resolve()
        else:
            if document != f"{module}.md":
                raise ValueError(f"Module document must be {module}.md or main: {document}")
            path = (design_dir / document).resolve()
            if path.parent != design_dir:
                raise ValueError(f"Module document escapes design directory: {document}")
        result[module] = path
    if not result:
        raise ValueError("Delivery scope has no applicable modules")
    return result


def design_documents(main_path: Path) -> list[Path]:
    if not main_path.is_file():
        return []
    try:
        paths = module_documents(main_path).values()
    except ValueError:
        return [main_path]
    return list(dict.fromkeys([main_path.resolve(), *(path for path in paths if path.is_file())]))


def impact_rows(text: str) -> list[tuple[str, str]]:
    return [(clean_cell(row[0]), clean_cell(row[1]).upper())
            for row in table_rows(text, "8. 文件影响范围") if len(row) >= 2]


def under_skill_root(rel_path: str) -> bool:
    return rel_path.replace("\\", "/").startswith(SKILL_ROOT_PREFIXES)


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
        # skill 根目录子树的新 skill 目录允许随交付创建；其余 CREATE 仍要求父目录存在。
        if not candidate.parent.exists() and not under_skill_root(rel_path):
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
    try:
        modules = module_documents(main_path)
    except ValueError as exc:
        findings.append(Finding("DELIVERY_SCOPE_INVALID", str(main_path), str(exc)))
        modules = {}
    if require_complete:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            findings.append(Finding("DESIGN_STATE_INVALID", str(state_path), str(exc)))
        else:
            if not isinstance(state, dict):
                findings.append(Finding("DESIGN_STATE_INVALID", str(state_path), "expected object"))
            else:
                applicable = state.get("applicable_stacks")
                completed = state.get("completed_stacks")
                valid = lambda value: isinstance(value, list) and all(isinstance(x, str) for x in value) and len(value) == len(set(value))
                if (state.get("status") != "complete" or not valid(applicable) or not valid(completed)
                        or set(applicable) != set(modules) or set(completed) != set(modules)
                        or "failed_stack" not in state or state.get("failed_stack") is not None):
                    findings.append(Finding("DESIGN_GENERATION_INCOMPLETE", str(state_path), "state and delivery modules must be complete and equal"))
    for heading in MAIN_HEADINGS:
        if heading not in main_text:
            findings.append(Finding("MAIN_HEADING_MISSING", str(main_path), heading))
    for module, path in modules.items():
        if path == main_path.resolve():
            continue
        if not path.is_file():
            findings.append(Finding("MODULE_DOC_MISSING", str(path), module))
            continue
        text = path.read_text(encoding="utf-8")
        documents[f"module:{module}"] = (path, text)
        if not impact_rows(text):
            findings.append(Finding("MODULE_IMPACT_EMPTY", str(path), module))
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

    contract = section(main_text, "4.3 跨端契约")
    content = "\n".join(contract.splitlines()[1:]).strip()
    if not content:
        findings.append(Finding("MAIN_CONTRACT_EMPTY", str(main_path), "declare a source or a reason for non-applicability"))

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
