#!/usr/bin/env python3
"""Resolve and create target-file-associated Figma workflow sessions."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def normalize_target(project: Path, target: Path) -> str:
    root = project.resolve()
    resolved = (root / target).resolve() if not target.is_absolute() else target.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"target file is outside project: {target}") from exc
    if not resolved.is_file():
        raise ValueError(f"target file does not exist: {target}")
    return relative.as_posix()


def clean_session_id(file_key: str, node_id: str) -> str:
    raw = f"{file_key}-{node_id.replace(':', '-')}"
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw).strip("-")
    if not cleaned:
        raise ValueError("fileKey/nodeId cannot produce an empty session id")
    return cleaned


def load_index(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"version": 1, "targets": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid figma index: {exc}") from exc
    if data.get("version") != 1 or not isinstance(data.get("targets"), dict):
        raise ValueError("invalid figma index: expected version=1 and targets object")
    return data


def target_entries(index: dict[str, Any], target: str) -> list[dict[str, Any]]:
    targets = index["targets"]
    lookup = target.casefold() if os.name == "nt" else target
    for key, entries in targets.items():
        candidate = key.casefold() if os.name == "nt" else key
        if candidate == lookup:
            if not isinstance(entries, list):
                raise ValueError(f"invalid figma index entries for {key}")
            return [entry for entry in entries if isinstance(entry, dict)]
    return []


def resolve(index: dict[str, Any], target: str) -> dict[str, Any]:
    active = [entry for entry in target_entries(index, target) if entry.get("status") == "active"]
    if not active:
        return {"status": "missing", "targetFile": target, "sessions": []}
    if len(active) == 1:
        return {"status": "unique", "targetFile": target, "session": active[0]}
    return {"status": "ambiguous", "targetFile": target, "sessions": active}


def create_session(
    project: Path,
    target: str,
    *,
    file_key: str,
    node_id: str,
    url: str,
    stage: str = "assets",
) -> dict[str, Any]:
    index_path = project / ".ai" / "figma" / "index.json"
    index = load_index(index_path)
    session_id = clean_session_id(file_key, node_id)
    entries = index["targets"].setdefault(target, [])
    if not isinstance(entries, list):
        raise ValueError(f"invalid figma index entries for {target}")
    if any(entry.get("sessionId") == session_id for entry in entries if isinstance(entry, dict)):
        return {"sessionId": session_id, "created": False}
    entries.append({"sessionId": session_id, "status": "active"})
    session_dir = project / ".ai" / "figma" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    session = {
        "version": 1,
        "sessionId": session_id,
        "fileKey": file_key,
        "mainNodeId": node_id,
        "url": url,
        "targetFile": target,
        "stage": stage,
        "specRevision": 0,
    }
    (session_dir / "session.json").write_text(
        json.dumps(session, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"sessionId": session_id, "created": True, "sessionPath": str(session_dir)}


def archive_session(project: Path, target: str, session_id: str) -> dict[str, Any]:
    index_path = project / ".ai" / "figma" / "index.json"
    index = load_index(index_path)
    entries = target_entries(index, target)
    matched = False
    for entry in entries:
        if entry.get("sessionId") == session_id:
            entry["status"] = "archived"
            matched = True
            break
    if not matched:
        raise ValueError(f"session is not associated with target: {session_id}")
    # target_entries returns the original entry objects, so the index is updated in place.
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"sessionId": session_id, "archived": True}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage .ai/figma target/session associations.")
    parser.add_argument("--project", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    resolve_parser = sub.add_parser("resolve")
    resolve_parser.add_argument("--target", required=True)
    create_parser = sub.add_parser("create")
    create_parser.add_argument("--target", required=True)
    create_parser.add_argument("--file-key", required=True)
    create_parser.add_argument("--node-id", required=True)
    create_parser.add_argument("--url", required=True)
    create_parser.add_argument(
        "--stage", choices=["assets", "motion"], default="assets",
        help="initial session stage; assets for restore chain, motion for standalone t-figma-ux",
    )
    archive_parser = sub.add_parser("archive")
    archive_parser.add_argument("--target", required=True)
    archive_parser.add_argument("--session-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project = Path(args.project).resolve()
    try:
        target = normalize_target(project, Path(args.target))
        index_path = project / ".ai" / "figma" / "index.json"
        if args.command == "resolve":
            result = resolve(load_index(index_path), target)
        elif args.command == "create":
            result = create_session(
                project, target, file_key=args.file_key, node_id=args.node_id,
                url=args.url, stage=args.stage,
            )
        else:
            result = archive_session(project, target, args.session_id)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 3 if result.get("status") == "ambiguous" else 0


if __name__ == "__main__":
    sys.exit(main())
