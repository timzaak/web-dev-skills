#!/usr/bin/env python3
"""
将 Markdown 文件中的相对路径链接转换为从项目根目录开始的路径。
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def resolve_to_root(source_file: Path, relative_path: str) -> str:
    """
    将相对路径转换为从项目根目录开始的路径。

    例如：
    - docs/prd/billing/shopify-pay.md + ./billing.md -> /docs/prd/billing/billing.md
    - spec/00-index.md + ./core/environment-and-testing-guide.md -> /spec/core/environment-and-testing-guide.md
    - docs/prd/billing/shopify-pay.md + ../../spec/backend/ -> /spec/backend/
    - skills/t-backend-test-run/README.md + ../../../spec/ -> /spec/
    """
    # 如果已经是根目录路径（以 / 开头），直接返回
    if relative_path.startswith("/"):
        return relative_path

    # 如果已经是根目录路径（以 docs/, spec/, skills/, agents/ 等开头），添加 / 前缀
    root_dirs = ["docs", "spec", "skills", "agents", "protocols", "commands", ".claude", "backend", "frontend", "demo", "scripts", ".ai"]
    if any(relative_path.startswith(d + "/") or relative_path == d for d in root_dirs):
        return "/" + relative_path

    if not (relative_path.startswith("../") or relative_path.startswith("./")):
        # 普通相对路径，直接使用
        return relative_path

    # 解析相对路径：先解析 .. 和 . 部分，然后计算到根目录的路径
    path = source_file.parent.resolve()
    parts = relative_path.split("/")
    resolved_parts = []

    for part in parts:
        if part == "..":
            path = path.parent
        elif part == ".":
            continue
        else:
            resolved_parts.append(part)

    # 计算从项目根目录的相对路径
    try:
        root_relative = path.relative_to(PROJECT_ROOT)
        if resolved_parts:
            if str(root_relative) == ".":
                return "/" + "/".join(resolved_parts)
            else:
                return "/" + str(root_relative).replace("\\", "/") + "/" + "/".join(resolved_parts)
        return "/" + str(root_relative).replace("\\", "/")
    except ValueError:
        # 如果无法计算相对路径，保持原样
        return relative_path


def fix_file(file_path: Path) -> int:
    """修复单个文件中的相对路径，返回修复的数量。"""
    content = read_file_safe(file_path)
    lines = content.splitlines(keepends=True)
    fixed_count = 0

    for i, line in enumerate(lines):
        # 跳过代码块
        if line.strip().startswith("```"):
            continue

        def replace_link(match):
            nonlocal fixed_count
            text = match.group(1)
            url = match.group(2)

            # 跳过外部链接、锚点等
            if url.startswith(("http://", "https://", "ftp://", "mailto:", "#")):
                return match.group(0)

            # 跳过不包含 ../ 或 ./ 的链接
            if not (url.startswith("../") or url.startswith("./")):
                return match.group(0)

            # 转换路径
            new_url = resolve_to_root(file_path, url)
            if new_url != url:
                fixed_count += 1
            return f"[{text}]({new_url})"

        lines[i] = LINK_PATTERN.sub(replace_link, line)

    if fixed_count > 0:
        file_path.write_text("".join(lines), encoding="utf-8")

    return fixed_count


def read_file_safe(file_path: Path) -> str:
    """安全读取文件，尝试多种编码。"""
    encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
    for encoding in encodings:
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法解码文件: {file_path}")


def main():
    # 查找所有包含相对路径的 md 文件
    md_files = []
    for md_file in PROJECT_ROOT.rglob("*.md"):
        # 跳过一些目录
        if any(part in md_file.parts for part in ["node_modules", ".git", "dist", "build", "target", ".venv"]):
            continue

        try:
            content = read_file_safe(md_file)
            if ("../" in content or "./" in content) and "](" in content:
                md_files.append(md_file)
        except Exception as e:
            print(f"警告: 跳过文件 {md_file.relative_to(PROJECT_ROOT)}: {e}")

    print(f"找到 {len(md_files)} 个包含相对路径的 Markdown 文件")

    total_fixed = 0
    for md_file in sorted(md_files):
        fixed = fix_file(md_file)
        if fixed > 0:
            relative_path = md_file.relative_to(PROJECT_ROOT)
            print(f"  {relative_path}: 修复了 {fixed} 个链接")
            total_fixed += fixed

    print(f"\n总计修复了 {total_fixed} 个相对路径链接")


if __name__ == "__main__":
    main()
