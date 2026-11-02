"""Pi resource recognition and local checks shared by push and release.

Workflow applicability is defined in protocols/pi-project-contract.md. These
helpers recognize existing resources; they do not infer a feature's scope.
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

from lib.cli import require_executable


RESOURCE_DIRS = ("extensions", "skills", "prompts", "themes")
CODE_SUFFIXES = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}


def read_package(package_json: Path) -> dict:
    if not package_json.is_file():
        return {}
    data = json.loads(package_json.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected a package object: {package_json}")
    return data


def is_conventional_resource(path: str) -> bool:
    parts = PurePosixPath(path.replace("\\", "/")).parts
    if len(parts) < 2:
        return False
    resource, *rest = parts
    leaf = PurePosixPath(parts[-1])
    if resource == "extensions":
        return leaf.suffix in {".ts", ".js"} and (len(rest) == 1 or len(rest) == 2 and leaf.stem == "index")
    if resource == "skills":
        return leaf.name == "SKILL.md"
    return resource == "prompts" and leaf.suffix == ".md" or resource == "themes" and leaf.suffix == ".json"


def is_pi_package_root(package_json: Path, changed_paths: list[str] | None = None) -> bool:
    if not package_json.is_file():
        return False
    data = read_package(package_json)
    keywords = data.get("keywords")
    if isinstance(data.get("pi"), dict) or isinstance(keywords, list) and "pi-package" in keywords:
        return True
    # Changed paths also cover removal of the last conventional resource.
    if any(is_conventional_resource(path) for path in changed_paths or []):
        return True
    root = package_json.parent
    return any(
        is_conventional_resource(path.relative_to(root).as_posix())
        for name in RESOURCE_DIRS
        for path in (root / name).rglob("*")
        if path.is_file()
    )


def is_project_resource(path: str) -> bool:
    parts = PurePosixPath(path.replace("\\", "/")).parts
    return len(parts) >= 3 and parts[0] == ".pi" and parts[1] in RESOURCE_DIRS


def has_project_resources(root: Path) -> bool:
    return any((root / ".pi" / name).is_dir() for name in RESOURCE_DIRS)


def pi_check_commands(root: Path, changed_paths: list[str] | None = None) -> list[tuple[str, list[str]]]:
    """Select local gates; never fetch a compiler or require TS for text assets."""
    package = read_package(root / "package.json")
    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict):
        scripts = {}
    type_script = next((key for key in ("type-check:pi", "typecheck:pi", "type-check", "typecheck", "check") if key in scripts), None)
    if changed_paths is None:
        needs_types = type_script is not None or pi_type_sources(root)
    else:
        needs_types = any(PurePosixPath(path).suffix in CODE_SUFFIXES for path in changed_paths)
        config_changed = any(
            PurePosixPath(path).name in {"package.json", "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"}
            or PurePosixPath(path).name.startswith("tsconfig")
            for path in changed_paths
        )
        if config_changed:
            needs_types = needs_types or pi_type_sources(root) or type_script is not None

    commands: list[tuple[str, list[str]]] = []
    for label, script in (("lint", "lint"), ("type check", type_script if needs_types else None), ("build", "build")):
        if script in scripts:
            commands.append((f"pi {label}", [require_executable("npm", "npm.cmd"), "run", script]))
        elif label == "type check" and needs_types:
            compiler = root / "node_modules" / "typescript" / "bin" / "tsc"
            if not compiler.is_file() or not (root / "tsconfig.json").is_file():
                raise RuntimeError("pi code changes require a type-check/typecheck/check script, or local TypeScript and tsconfig.json; prepare the project checks before retrying.")
            commands.append(("pi type check", [require_executable("node"), str(compiler), "--noEmit"]))
    return commands


def pi_type_sources(root: Path) -> bool:
    manifest = read_package(root / "package.json").get("pi", {})
    if isinstance(manifest, dict) and manifest.get("extensions"):
        return True
    return any(
        path.suffix in CODE_SUFFIXES
        for base in (root / "extensions", root / ".pi" / "extensions", root / "src")
        for path in base.rglob("*") if path.is_file()
    )
