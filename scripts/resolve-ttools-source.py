#!/usr/bin/env python3
"""Resolve and verify the t-tools source worktree used as the single source of truth."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")


def worktree_root(candidate: Path) -> Path | None:
    result = git(candidate, "rev-parse", "--show-toplevel")
    if result.returncode:
        return None
    return Path(result.stdout.strip())


def verify_root(root: Path) -> str | None:
    """Return None when the worktree is a valid t-tools source, otherwise the failure reason."""
    manifest = root / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        return "missing .claude-plugin/plugin.json"
    try:
        name = json.loads(manifest.read_text(encoding="utf-8")).get("name")
    except (OSError, ValueError):
        return "unreadable .claude-plugin/plugin.json"
    if name != "t-tools":
        return f"plugin name is {name!r}, not 't-tools'"
    skill = root / "skills" / "t-skill" / "SKILL.md"
    if not skill.is_file():
        return "missing skills/t-skill/SKILL.md"
    if git(root, "ls-files", "--error-unmatch", "skills/t-skill/SKILL.md").returncode:
        return "skills/t-skill/SKILL.md is not tracked by Git"
    return None


def resolve(candidates: list[Path]) -> dict:
    attempts = []
    for label, candidate in candidates:
        if not candidate.exists():
            attempts.append({"candidate": str(candidate), "source": label, "reason": "path does not exist"})
            continue
        root = worktree_root(candidate)
        if root is None:
            attempts.append({"candidate": str(candidate), "source": label, "reason": "not inside a Git worktree"})
            continue
        reason = verify_root(root)
        if reason:
            attempts.append({"candidate": str(candidate), "source": label, "reason": reason})
            continue
        revision = git(root, "rev-parse", "HEAD").stdout.strip()
        dirty = bool(git(root, "status", "--porcelain").stdout.strip())
        return {"status": "ok", "root": str(root.resolve()), "revision": revision,
                "dirty": dirty, "source": label}
    return {"status": "error", "reason": "no verified t-tools worktree", "candidates": attempts}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", nargs="*", type=Path,
                        help="explicit candidate paths checked before the environment and the working directory")
    args = parser.parse_args(argv)
    candidates = [(f"argument:{path}", path) for path in args.candidates]
    if not candidates:
        for variable in ("CLAUDE_PLUGIN_ROOT", "T_TOOLS_ROOT"):
            value = os.environ.get(variable)
            if value:
                candidates.append((f"env:{variable}", Path(value)))
        candidates.append(("cwd", Path.cwd()))
    result = resolve(candidates)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
