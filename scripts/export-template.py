#!/usr/bin/env python3
"""Export an optional, version-pinned domain template as a standalone plugin."""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path("templates/project-profiles")
ORIGIN_FILE = ".t-tools-template.json"


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def safe_name(name: str) -> str:
    path = PurePosixPath(name)
    if (name in {"", ".", ".."} or path.is_absolute() or "\\" in name or ":" in name
            or any(part in {"..", ".git"} for part in path.parts)
            or path.as_posix() != name):
        raise ValueError(f"Unsafe template path: {name}")
    return name


def load_manifest(root: Path, profile_id: str) -> tuple[Path, dict]:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", profile_id):
        raise ValueError("Invalid template ID")
    directory = root / CATALOG / profile_id
    path = directory / "template.json"
    if not path.is_file():
        raise ValueError(f"Unknown template: {profile_id}; use the list command")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("id") != profile_id:
        raise ValueError(f"Invalid template manifest: {path}")
    if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("upstream_revision", ""))):
        raise ValueError("upstream_revision must be a full Git commit ID")
    paths = manifest.get("source_paths")
    if not isinstance(paths, list) or not paths or not all(isinstance(x, str) for x in paths):
        raise ValueError("source_paths must be a nonempty list of paths")
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate source_paths")
    for name in paths:
        safe_name(name)
        source = directory / "files" / name
        if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to((directory / "files").resolve()):
            raise ValueError(f"Missing or unsafe template source: {name}")
    return directory, manifest


def archive_files(root: Path, revision: str) -> dict[str, bytes]:
    try:
        archive = git(root, "-c", "core.autocrlf=false", "archive", "--format=tar", revision)
    except ValueError as exc:
        raise ValueError(f"Template baseline unavailable: {revision}. Fetch its Git history before export. {exc}") from exc
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as source:
        for member in source.getmembers():
            safe_name(member.name.rstrip("/"))
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f"Unsupported archive entry: {member.name}")
            stream = source.extractfile(member)
            assert stream is not None
            files[member.name] = stream.read()
    return files


def export_template(root: Path, profile_id: str, output: Path, *, dry_run: bool = False) -> dict:
    directory, manifest = load_manifest(root, profile_id)
    output = output.expanduser().resolve()
    root = root.resolve()
    if output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError("Output must be outside the source repository and cannot contain it")
    if output.exists() and not output.is_dir():
        raise ValueError("Output is not a directory")
    files = archive_files(root, manifest["upstream_revision"])
    for name in manifest["source_paths"]:
        files[name] = (directory / "files" / name).read_bytes()
    origin = {"template": profile_id, "upstream_revision": manifest["upstream_revision"]}
    files[ORIGIN_FILE] = (json.dumps(origin, indent=2) + "\n").encode("utf-8")
    summary = {**origin, "output": str(output), "file_count": len(files)}
    if output.exists() and any(output.iterdir()):
        unchanged = all((output / name).is_file() and not (output / name).is_symlink()
                        and (output / name).resolve().is_relative_to(output)
                        and (output / name).read_bytes() == data for name, data in files.items())
        if unchanged:
            return {**summary, "status": "unchanged"}
        raise ValueError("Output contains different files; export to a new directory. Existing files were preserved")
    if dry_run:
        return {**summary, "status": "planned"}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".t-tools-export-", dir=output.parent) as temporary:
        stage = Path(temporary) / "plugin"
        stage.mkdir()
        for name, data in files.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        # The destination is never populated incrementally. A failed write leaves it intact.
        if output.exists():
            output.rmdir()
        stage.replace(output)
    return {**summary, "status": "exported"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List optional templates")
    export = commands.add_parser("export", help="Create a standalone plugin using the template's pinned baseline")
    export.add_argument("template")
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            profiles = []
            for path in sorted((REPO_ROOT / CATALOG).glob("*/template.json")):
                _, manifest = load_manifest(REPO_ROOT, path.parent.name)
                profiles.append({key: manifest[key] for key in ("id", "description", "upstream_revision")})
            print(json.dumps(profiles, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(export_template(REPO_ROOT, args.template, args.output, dry_run=args.dry_run), ensure_ascii=False))
    except (ValueError, OSError, tarfile.TarError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
