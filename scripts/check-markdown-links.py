#!/usr/bin/env python3
"""
Markdown 文档链接检查脚本。

功能：
1. 检查仓库内 Markdown 死链接
2. 检测禁止的相对路径（../）
3. 识别从入口文档不可达的 Markdown 文档
4. 识别完全未被其他 Markdown 文档直接引用的文档
"""

from __future__ import annotations

import argparse
import re
from collections import deque
from pathlib import Path
from typing import Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).parent.parent

EXCLUDE_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "target",
    ".venv",
    "__pycache__",
    ".ai",
    "human",
}

DEFAULT_REPORT_PATH = Path(".ai/check-markdown-links-report.md")
ROOT_DOCS = {"CLAUDE.md", "AGENTS.md"}
INDEX_PATTERNS = {"00-index.md", "index.md", "INDEX.md"}
README_PATTERNS = {"README.md", "_README.md"}

SEVERITY = {
    "P0": "严重 - 阻塞功能运行，必须立即修复",
    "P1": "重要 - 影响功能质量，应尽快修复",
    "P2": "一般 - 代码质量问题，可延后修复",
    "P3": "优化 - 改进建议，不影响功能",
}

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


class MarkdownLink:
    def __init__(self, text: str, url: str, line_number: int, source_file: Path):
        self.text = text
        self.url = url
        self.line_number = line_number
        self.source_file = source_file
        self.is_external = url.startswith(("http://", "https://", "ftp://", "mailto:"))
        self.is_anchor = "#" in url
        self.is_relative_path = url.startswith("../") or url.startswith("./")
        self.target_file, self.anchor = self._parse_target()

    def _parse_target(self) -> Tuple[str, str]:
        if self.is_external:
            return "", ""

        url = re.sub(r"^\w+:/", "", self.url)
        parts = url.split("#", 1)
        target = parts[0]
        anchor = parts[1] if len(parts) > 1 else ""
        return target, anchor

    def get_suggested_root_path(self) -> str:
        """获取建议的项目根路径"""
        if not self.is_relative_path:
            return self.url

        # 解析相对路径并转换为根路径
        path = self.source_file.parent.resolve()
        parts = self.target_file.split("/")
        resolved_parts = []

        for part in parts:
            if part == "..":
                path = path.parent
            elif part == ".":
                continue
            else:
                resolved_parts.append(part)

        try:
            root_relative = path.relative_to(PROJECT_ROOT)
            if resolved_parts:
                if str(root_relative) == ".":
                    return "/" + "/".join(resolved_parts)
                else:
                    return "/" + str(root_relative).replace("\\", "/") + "/" + "/".join(resolved_parts)
            return "/" + str(root_relative).replace("\\", "/")
        except ValueError:
            return self.url


def is_excluded(path: Path, extra_dirs: Set[str] | None = None, extra_files: Set[Path] | None = None) -> bool:
    rel = path.relative_to(PROJECT_ROOT)
    exclude_dirs = EXCLUDE_DIRS | (extra_dirs or set())
    if any(part in exclude_dirs for part in rel.parts):
        return True
    if extra_files and rel in extra_files:
        return True
    return False


def find_all_md_files(root: Path) -> List[Path]:
    md_files = []
    for path in root.rglob("*.md"):
        if is_excluded(path):
            continue
        md_files.append(path.resolve())
    return sorted(md_files)


def remove_inline_code(line: str) -> str:
    result = []
    in_backtick = False
    i = 0
    while i < len(line):
        char = line[i]
        if char == "`" and (i == 0 or line[i - 1] != "\\"):
            in_backtick = not in_backtick
            i += 1
            continue
        if not in_backtick:
            result.append(char)
        i += 1
    return "".join(result)


def should_skip_url(url: str) -> bool:
    if url in ("待补充（TBD）", "TBD", "待补充"):
        return True
    if url.startswith(("![[", "[[[")):
        return True
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", url) and not re.search(r"[/.]", url):
        return True
    if "&self" in url or "identity:" in url or ("&" in url and ")" in url):
        return True
    return False


def extract_links_from_file(file_path: Path) -> List[MarkdownLink]:
    links: List[MarkdownLink] = []
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    in_fenced_block = False
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fenced_block = not in_fenced_block
            continue
        if in_fenced_block:
            continue

        searchable_line = remove_inline_code(line)
        for match in LINK_PATTERN.finditer(searchable_line):
            text = match.group(1)
            url = match.group(2).strip()
            if should_skip_url(url):
                continue
            links.append(MarkdownLink(text, url, line_num, file_path))

    return links


def resolve_relative_path(source_file: Path, target: str) -> Path:
    if not target:
        return source_file.resolve()
    # 如果以 / 开头，表示从项目根目录开始的绝对路径
    if target.startswith("/"):
        return (PROJECT_ROOT / target[1:]).resolve()
    return (source_file.parent / target).resolve()


def path_exists(target: Path) -> bool:
    return target.exists()


def file_exists(target: Path) -> bool:
    return target.exists() and target.is_file()


def is_directory_link(url: str) -> bool:
    return url.endswith("/")


def slugify_heading(text: str) -> str:
    slug = text.strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^\w\-\u4e00-\u9fff]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def anchor_exists(target_file: Path, anchor: str) -> bool:
    if not anchor:
        return True
    if not file_exists(target_file):
        return False

    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception:
        return False

    normalized_anchor = slugify_heading(anchor)
    for line in content.splitlines():
        if line.strip().startswith("#"):
            title = re.sub(r"^#+\s*", "", line.strip())
            if slugify_heading(title) == normalized_anchor:
                return True
    return False


def get_file_type(file_path: Path) -> str:
    relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()

    if file_path.name in ROOT_DOCS:
        return "root"
    if is_repo_index_doc(file_path):
        return "index"
    if file_path.name in README_PATTERNS:
        return "readme"
    if relative_path.startswith("agents/") or relative_path.startswith(".claude/agents/"):
        return "agent"
    if relative_path.startswith("commands/") or relative_path.startswith(".claude/commands/"):
        return "command"
    if relative_path.startswith("skills/") or relative_path.startswith(".claude/skills/"):
        return "skill"
    if relative_path.startswith("protocols/") or relative_path.startswith(".claude/protocols/"):
        return "protocol"
    if relative_path.startswith("spec/"):
        return "spec"
    if relative_path.startswith("docs/"):
        return "doc"
    if relative_path.startswith("demo/"):
        return "demo"
    return "other"


def is_repo_index_doc(file_path: Path) -> bool:
    rel = file_path.relative_to(PROJECT_ROOT).as_posix()
    if file_path.name not in INDEX_PATTERNS:
        return False
    return rel.startswith("docs/") or rel.startswith("spec/")


def is_readme_doc(file_path: Path) -> bool:
    return file_path.name in README_PATTERNS


def is_high_priority_source(file_path: Path) -> bool:
    return file_path.name in ROOT_DOCS or is_repo_index_doc(file_path)


def classify_severity(link: MarkdownLink, target_path_exists: bool, target_anchor_exists: bool) -> str | None:
    if link.is_external or link.url in ("待补充（TBD）", "TBD", "待补充"):
        return None

    source_file_type = get_file_type(link.source_file)

    if is_directory_link(link.url):
        if target_path_exists:
            return None
        if is_high_priority_source(link.source_file):
            return "P0"
        return "P2"

    if not target_path_exists:
        if is_high_priority_source(link.source_file):
            return "P0"
        if source_file_type in {"spec", "agent", "command", "protocol"}:
            return "P1"
        return "P2"

    if link.is_anchor and not target_anchor_exists:
        if source_file_type in {"spec", "agent", "command", "protocol"}:
            return "P1"
        return "P2"

    return None


def is_entry_doc(file_path: Path) -> bool:
    rel = file_path.relative_to(PROJECT_ROOT).as_posix()
    if file_path.name in ROOT_DOCS:
        return True
    if is_repo_index_doc(file_path):
        return True
    if is_readme_doc(file_path):
        return True
    if rel.startswith("agents/") or rel.startswith(".claude/agents/"):
        return True
    if rel.startswith("commands/") or rel.startswith(".claude/commands/"):
        return True
    if (rel.startswith("skills/") or rel.startswith(".claude/skills/")) and file_path.name == "SKILL.md":
        return True
    return False


def should_skip_orphan_check(file_path: Path) -> bool:
    return is_excluded(file_path)


def build_reachable_docs(entry_docs: Set[Path], edges: Dict[Path, Set[Path]]) -> Set[Path]:
    reachable: Set[Path] = set()
    queue: deque[Path] = deque(sorted(entry_docs))

    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        for target in sorted(edges.get(current, set())):
            if target not in reachable:
                queue.append(target)

    return reachable


def format_path(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("/", "\\")


def generate_report(
    md_files: List[Path],
    all_links: List[MarkdownLink],
    dead_links: List[dict],
    entry_unreachable_files: List[dict],
    unreferenced_files: List[dict],
    relative_path_links: List[MarkdownLink],
) -> str:
    dead_links_by_severity = {"P0": [], "P1": [], "P2": [], "P3": []}
    dead_link_by_identity = {}
    for dead_link in dead_links:
        dead_links_by_severity[dead_link["severity"]].append(dead_link)
        identity = (
            dead_link["link"].source_file,
            dead_link["link"].line_number,
            dead_link["link"].url,
        )
        dead_link_by_identity[identity] = dead_link["severity"]

    lines = []
    lines.append("# Markdown 文档链接检查报告\n")
    lines.append("## 摘要\n")
    lines.append("| 指标 | 数量 |")
    lines.append("|------|------|")
    lines.append(f"| 检查的文档总数 | {len(md_files)} |")
    lines.append(f"| 检查的链接总数 | {len(all_links)} |")
    lines.append(f"| 相对路径链接数量 | {len(relative_path_links)} |")
    lines.append(f"| 死链接数量 | {len(dead_links)} |")
    lines.append(f"| 入口不可达文档数量 | {len(entry_unreachable_files)} |")
    lines.append(f"| 完全未被引用文档数量 | {len(unreferenced_files)} |\n")

    if relative_path_links:
        lines.append("## 相对路径链接\n")
        lines.append("**说明**: 禁止使用 `../` 或 `./` 相对路径，应使用以 `/` 开头的项目根路径。\n")
        lines.append("| 文件 | 行号 | 当前链接 | 建议路径 |")
        lines.append("|------|------|----------|----------|")
        for link in relative_path_links:
            suggested = link.get_suggested_root_path()
            lines.append(f"| `{format_path(link.source_file)}` | {link.line_number} | `{link.url}` | `{suggested}` |")
        lines.append("")

    if dead_links:
        lines.append("## 死链接详情\n")
        for severity in ["P0", "P1", "P2"]:
            if not dead_links_by_severity[severity]:
                continue
            lines.append(f"### {severity} - {SEVERITY[severity].split(' - ')[0]}\n")
            lines.append(f"**{SEVERITY[severity]}**\n")
            for dead_link in dead_links_by_severity[severity]:
                link = dead_link["link"]
                lines.append(f"- **文件**: `{format_path(link.source_file)}`")
                lines.append(f"  - **行号**: {link.line_number}")
                lines.append(f"  - **链接**: `[{link.text}]({link.url})`")
                lines.append(f"  - **目标**: `{dead_link['target']}`")
                lines.append(f"  - **问题**: {dead_link['problem']}")
                lines.append("  - **建议**: 检查路径或创建文件\n")

    if entry_unreachable_files:
        lines.append("## 入口不可达文档\n")
        lines.append("| 文件 | 类型 | 建议 |")
        lines.append("|------|------|------|")
        for item in entry_unreachable_files:
            lines.append(f"| `{item['relative_path']}` | {item['type']} | 补充入口链路或确认是否应排除 |")
        lines.append("")

    if unreferenced_files:
        lines.append("## 完全未被引用文档\n")
        lines.append("| 文件 | 类型 | 建议 |")
        lines.append("|------|------|------|")
        for item in unreferenced_files:
            lines.append(f"| `{item['relative_path']}` | {item['type']} | 确认是否需要被其他文档直接引用 |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="检查 Markdown 死链接和入口可达性。")
    parser.add_argument("--report", type=Path, help="可选：输出 Markdown 报告到指定路径。")
    args = parser.parse_args()

    print("Markdown 文档链接检查")
    print("=" * 60)

    print("\n1. 查找 Markdown 文件...")
    md_files = find_all_md_files(PROJECT_ROOT)
    print(f"   找到 {len(md_files)} 个 .md 文件")

    print("\n2. 提取链接...")
    all_links: List[MarkdownLink] = []
    for md_file in md_files:
        all_links.extend(extract_links_from_file(md_file))
    print(f"   提取 {len(all_links)} 个链接")

    print("\n3. 检测相对路径...")
    relative_path_links: List[MarkdownLink] = []
    for link in all_links:
        if link.is_relative_path:
            relative_path_links.append(link)
    print(f"   发现 {len(relative_path_links)} 个相对路径链接")

    print("\n4. 验证链接...")
    dead_links: List[dict] = []
    valid_links: List[MarkdownLink] = []
    valid_edges: Dict[Path, Set[Path]] = {}
    referenced_files: Set[Path] = set()

    for link in all_links:
        if link.is_external or link.url in ("待补充（TBD）", "TBD", "待补充"):
            continue

        target_path = resolve_relative_path(link.source_file, link.target_file)
        target_path_exists = path_exists(target_path)
        target_file_exists = file_exists(target_path)
        target_anchor_exists = True
        if link.is_anchor and target_file_exists:
            target_anchor_exists = anchor_exists(target_path, link.anchor)

        severity = classify_severity(link, target_path_exists, target_anchor_exists)
        if severity:
            dead_links.append(
                {
                    "link": link,
                    "target": str(target_path),
                    "path_exists": target_path_exists,
                    "file_exists": target_file_exists,
                    "anchor_exists": target_anchor_exists,
                    "severity": severity,
                    "problem": "路径不存在"
                    if not target_path_exists
                    else ("文件不存在" if not target_file_exists else "锚点不存在"),
                }
            )
            continue

        valid_links.append(link)
        if target_file_exists:
            resolved_target = target_path.resolve()
            valid_edges.setdefault(link.source_file.resolve(), set()).add(resolved_target)
            referenced_files.add(resolved_target)

    print(f"   有效链接: {len(valid_links)}")
    print(f"   死链接: {len(dead_links)}")

    print("\n5. 检测入口可达性与直接引用...")
    orphan_candidates = [f for f in md_files if not should_skip_orphan_check(f)]
    entry_docs = {f for f in orphan_candidates if is_entry_doc(f)}
    reachable_docs = build_reachable_docs(entry_docs, valid_edges)

    entry_unreachable_files = []
    unreferenced_files = []
    for md_file in orphan_candidates:
        file_type = get_file_type(md_file)
        if is_entry_doc(md_file):
            continue

        if md_file not in reachable_docs:
            entry_unreachable_files.append(
                {
                    "file": md_file,
                    "type": file_type,
                    "relative_path": format_path(md_file),
                }
            )

        if md_file not in referenced_files:
            unreferenced_files.append(
                {
                    "file": md_file,
                    "type": file_type,
                    "relative_path": format_path(md_file),
                }
            )

    print(f"   入口不可达文档: {len(entry_unreachable_files)}")
    print(f"   完全未被引用文档: {len(unreferenced_files)}")

    print("\n6. 输出结果...")
    report_arg = args.report or DEFAULT_REPORT_PATH
    report_path = report_arg if report_arg.is_absolute() else (PROJECT_ROOT / report_arg)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        generate_report(md_files, all_links, dead_links, entry_unreachable_files, unreferenced_files, relative_path_links),
        encoding="utf-8",
    )
    print(f"   报告已写入: {report_path}")

    print("\n" + "=" * 60)
    print("检查摘要")
    print("=" * 60)
    print(f"文档总数: {len(md_files)}")
    print(f"链接总数: {len(all_links)}")
    print(f"相对路径链接: {len(relative_path_links)}")
    print(f"有效链接: {len(valid_links)}")
    print(f"死链接: {len(dead_links)}")
    print(f"入口不可达文档: {len(entry_unreachable_files)}")
    print(f"完全未被引用文档: {len(unreferenced_files)}")

    if relative_path_links:
        print("\n相对路径链接 (前5个):")
        for link in relative_path_links[:5]:
            suggested = link.get_suggested_root_path()
            print(f"  - {format_path(link.source_file)}:{link.line_number}")
            print(f"    当前: {link.url}")
            print(f"    建议: {suggested}")
        if len(relative_path_links) > 5:
            print(f"  ... 还有 {len(relative_path_links) - 5} 个")

    if dead_links:
        print("\n按严重性分类:")
        for severity in ["P0", "P1", "P2"]:
            count = len([item for item in dead_links if item["severity"] == severity])
            if count:
                print(f"  {severity}: {count} 个")

    if entry_unreachable_files:
        print("\n入口不可达文档 (前5个):")
        for item in entry_unreachable_files[:5]:
            print(f"  - {item['relative_path']} ({item['type']})")
        if len(entry_unreachable_files) > 5:
            print(f"  ... 还有 {len(entry_unreachable_files) - 5} 个")

    if unreferenced_files:
        print("\n完全未被引用文档 (前5个):")
        for item in unreferenced_files[:5]:
            print(f"  - {item['relative_path']} ({item['type']})")
        if len(unreferenced_files) > 5:
            print(f"  ... 还有 {len(unreferenced_files) - 5} 个")


if __name__ == "__main__":
    main()
