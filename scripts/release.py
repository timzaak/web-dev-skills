#!/usr/bin/env python
import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from lib.cli import require_executable, run_cmd
from lib.paths import REPO_ROOT


SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True)
class Semver:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, text: str) -> "Semver":
        match = SEMVER_RE.fullmatch(text.strip())
        if not match:
            raise ValueError(f"Invalid version '{text}'. Use X.Y.Z or vX.Y.Z.")
        return cls(*(int(part) for part in match.groups()))

    def bump_patch(self) -> "Semver":
        return Semver(self.major, self.minor, self.patch + 1)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class FileChange:
    path: Path
    before: str | None
    after: str


def git(*args: str, capture: bool = False):
    git_bin = require_executable("git")
    return run_cmd([git_bin, *args], cwd=REPO_ROOT, capture=capture)


def ensure_success(result, message: str) -> None:
    if result.returncode != 0:
        raise RuntimeError(message)


def ensure_on_main() -> None:
    result = git("branch", "--show-current", capture=True)
    ensure_success(result, "Unable to determine current git branch.")
    branch = result.stdout.strip()
    if branch != "main":
        raise RuntimeError(f"Release must run on main, current branch is '{branch}'.")


def ensure_clean_worktree() -> None:
    result = git("status", "--porcelain", capture=True)
    ensure_success(result, "Unable to inspect git status.")
    if result.stdout.strip():
        raise RuntimeError("Working tree is not clean. Commit or stash changes before release.")


def ensure_remote_access() -> None:
    result = git("ls-remote", "--exit-code", "origin", capture=True)
    ensure_success(result, "Remote 'origin' is not accessible.")


def list_tags() -> list[str]:
    result = git("tag", "--list", capture=True)
    ensure_success(result, "Unable to list git tags.")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def latest_semver_tag(tags: list[str]) -> Semver | None:
    versions: list[Semver] = []
    for tag in tags:
        try:
            versions.append(Semver.parse(tag))
        except ValueError:
            continue
    if not versions:
        return None
    return max(versions, key=lambda item: (item.major, item.minor, item.patch))


def ensure_tag_available(version: str, tags: list[str]) -> None:
    conflicts = [tag for tag in (version, f"v{version}") if tag in tags]
    if conflicts:
        raise RuntimeError(f"Tag conflict: {', '.join(conflicts)} already exists.")

    remote = git("ls-remote", "--tags", "origin", version, f"v{version}", capture=True)
    ensure_success(remote, "Unable to inspect remote tags.")
    remote_conflicts = []
    for line in remote.stdout.splitlines():
        if "refs/tags/" in line:
            remote_conflicts.append(line.rsplit("refs/tags/", 1)[1].removesuffix("^{}"))
    if remote_conflicts:
        unique = sorted(set(remote_conflicts))
        raise RuntimeError(f"Remote tag conflict: {', '.join(unique)} already exists.")


def read_current_cargo_version(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    in_workspace_package = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[workspace.package]":
            in_workspace_package = True
            continue
        if in_workspace_package and stripped.startswith("["):
            return None
        if in_workspace_package:
            match = re.match(r'\s*version\s*=\s*"([^"]+)"', line)
            if match:
                return match.group(1)
    return None


def update_cargo_version(path: Path, version: str) -> FileChange | None:
    if not path.is_file():
        return None

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    in_workspace_package = False
    before: str | None = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "[workspace.package]":
            in_workspace_package = True
            continue
        if in_workspace_package and stripped.startswith("["):
            break
        if in_workspace_package:
            newline = "\n" if line.endswith("\n") else ""
            body = line[:-1] if newline else line
            if body.endswith("\r"):
                body = body[:-1]
                newline = "\r\n"
            match = re.match(r'(\s*version\s*=\s*")([^"]+)(".*)', body)
            if match:
                before = match.group(2)
                lines[index] = f"{match.group(1)}{version}{match.group(3)}{newline}"
                path.write_text("".join(lines), encoding="utf-8")
                return FileChange(path, before, version)

    return None


def update_package_json(path: Path, version: str) -> FileChange | None:
    if not path.is_file():
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    before = data.get("version")
    data["version"] = version
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return FileChange(path, before, version)


def update_version_files(version: str) -> list[FileChange]:
    changes: list[FileChange] = []

    for cargo_path in (
        REPO_ROOT / "backend" / "Cargo.toml",
        REPO_ROOT / "Cargo.toml",
    ):
        cargo_change = update_cargo_version(cargo_path, version)
        if cargo_change:
            changes.append(cargo_change)

    for package_path in (
        REPO_ROOT / "frontend" / "package.json",
        REPO_ROOT / "demo" / "package.json",
    ):
        package_change = update_package_json(package_path, version)
        if package_change:
            changes.append(package_change)

    if not changes:
        raise RuntimeError("No supported version files found.")
    return changes


def command_exists(command: str) -> bool:
    try:
        require_executable(command, f"{command}.cmd")
        return True
    except RuntimeError:
        return False


def run_validation() -> None:
    commands: list[tuple[list[str], Path]] = []

    cargo_dir = next(
        (d for d in (REPO_ROOT / "backend", REPO_ROOT) if (d / "Cargo.toml").is_file()),
        None,
    )
    if cargo_dir is not None:
        cargo = require_executable("cargo")
        commands.append(([cargo, "check"], cargo_dir))

    npm = None
    if command_exists("npm"):
        npm = require_executable("npm", "npm.cmd")

    for app_dir in (REPO_ROOT / "frontend", REPO_ROOT / "demo"):
        package_json = app_dir / "package.json"
        if not package_json.is_file() or npm is None:
            continue
        data = json.loads(package_json.read_text(encoding="utf-8"))
        scripts = data.get("scripts", {})
        if "typecheck" in scripts:
            commands.append(([npm, "run", "typecheck"], app_dir))
        if "lint" in scripts:
            commands.append(([npm, "run", "lint"], app_dir))

    if not commands:
        print("No validation commands detected; skipping validation.")
        return

    for cmd, cwd in commands:
        print(f"Running: {' '.join(cmd)} (cwd: {cwd.relative_to(REPO_ROOT)})", flush=True)
        result = run_cmd(cmd, cwd=cwd)
        if result.returncode != 0:
            raise RuntimeError(f"Validation failed: {' '.join(cmd)}")


def commit_tag_and_push(version: str, push: bool) -> str:
    release_tag = f"v{version}"
    release_paths = [
        "Cargo.toml",
        "Cargo.lock",
        "backend/Cargo.toml",
        "backend/Cargo.lock",
        "frontend/package.json",
        "frontend/package-lock.json",
        "demo/package.json",
        "demo/package-lock.json",
    ]
    existing_paths = [path for path in release_paths if (REPO_ROOT / path).exists()]
    add = git("add", *existing_paths)
    ensure_success(add, "Unable to stage release files.")

    staged = git("diff", "--cached", "--quiet")
    if staged.returncode == 0:
        raise RuntimeError(f"No version file changes detected for {version}.")

    commit = git("commit", "-m", f"chore: bump version to {version}")
    ensure_success(commit, "Unable to create release commit.")

    tag = git("tag", release_tag)
    ensure_success(tag, f"Unable to create tag {release_tag}.")

    rev = git("rev-parse", "--short", "HEAD", capture=True)
    ensure_success(rev, "Unable to resolve release commit hash.")
    commit_hash = rev.stdout.strip()

    if push:
        push_commit = git("push")
        if push_commit.returncode != 0:
            raise RuntimeError(f"Push failed. Commit {commit_hash} and tag {release_tag} remain local.")

        push_tag = git("push", "origin", release_tag)
        if push_tag.returncode != 0:
            raise RuntimeError(f"Tag push failed. Commit {commit_hash} and tag {release_tag} remain local.")

    return commit_hash


def resolve_target_version(raw_version: str | None, assume_yes: bool, tags: list[str]) -> str:
    if raw_version:
        version = str(Semver.parse(raw_version))
        if raw_version.startswith("v"):
            print(f"Normalized input version {raw_version} -> {version}; release tag will be v{version}.")
        return version

    latest = latest_semver_tag(tags)
    recommendation = str(latest.bump_patch() if latest else Semver(0, 1, 0))
    if not assume_yes:
        latest_text = str(latest) if latest else "none"
        raise RuntimeError(
            f"Recommended version is {recommendation} based on latest semver tag {latest_text}. "
            "Re-run with this version or pass --yes to accept the recommendation."
        )
    return recommendation


def main() -> int:
    parser = argparse.ArgumentParser(description="Release project version with v-prefixed git tags.")
    parser.add_argument("version", nargs="?", help="Target version, X.Y.Z or vX.Y.Z. Final tag is always vX.Y.Z.")
    parser.add_argument("--yes", action="store_true", help="Accept the auto-recommended version when version is omitted.")
    parser.add_argument("--no-push", action="store_true", help="Create the release commit and tag locally without pushing.")
    parser.add_argument("--dry-run", action="store_true", help="Run preflight checks and print the resolved version without editing files.")
    args = parser.parse_args()

    try:
        ensure_on_main()
        ensure_clean_worktree()
        ensure_remote_access()
        tags = list_tags()
        version = resolve_target_version(args.version, args.yes, tags)
        ensure_tag_available(version, tags)

        print(f"Release version: {version}")
        release_tag = f"v{version}"
        print(f"Release tag: {release_tag}")
        if args.dry_run:
            return 0

        changes = update_version_files(version)
        for change in changes:
            rel_path = change.path.relative_to(REPO_ROOT)
            before = change.before if change.before is not None else "<missing>"
            print(f"Updated {rel_path}: {before} -> {change.after}")

        run_validation()
        commit_hash = commit_tag_and_push(version, push=not args.no_push)
        push_text = "pushed" if not args.no_push else "created locally"
        print(f"Release {version} {push_text}: commit {commit_hash}, tag {release_tag}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
