#!/usr/bin/env python
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from lib.cli import require_executable, run_cmd
from lib.java_backend import build_quality_commands, detect_build_tool
from lib.paths import REPO_ROOT


@dataclass(frozen=True)
class Step:
    name: str
    command: list[str]
    cwd: Path
    optional: bool = False


def git(*args: str, capture: bool = False):
    git_bin = require_executable("git")
    return run_cmd([git_bin, *args], cwd=REPO_ROOT, capture=capture)


def ensure_success(result, message: str) -> None:
    if result.returncode != 0:
        raise RuntimeError(message)


def split_z_output(text: str) -> list[str]:
    return [item for item in text.split("\0") if item]


def changed_files() -> list[str]:
    tracked = git("diff", "--name-only", "-z", "HEAD", capture=True)
    ensure_success(tracked, "Unable to inspect tracked git changes.")

    untracked = git("ls-files", "--others", "--exclude-standard", "-z", capture=True)
    ensure_success(untracked, "Unable to inspect untracked git files.")

    files = split_z_output(tracked.stdout) + split_z_output(untracked.stdout)
    return sorted(dict.fromkeys(path.replace("\\", "/") for path in files))


def git_status_short() -> str:
    result = git("status", "--short", capture=True)
    ensure_success(result, "Unable to inspect git status.")
    return result.stdout.strip()


def detect_areas(files: list[str]) -> set[str]:
    areas: set[str] = set()
    for path in files:
        if path.startswith("backend/"):
            areas.add("backend")
        elif path.startswith("frontend/"):
            areas.add("frontend")
        elif path.startswith("demo/"):
            areas.add("demo")
    return areas


def read_package_scripts(package_json: Path) -> dict[str, str]:
    if not package_json.is_file():
        raise RuntimeError(f"Missing package.json: {package_json.relative_to(REPO_ROOT)}")
    data = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {str(key): str(value) for key, value in scripts.items()}


def npm_script_step(name: str, app_dir: Path, script: str, *, optional: bool = False) -> Step | None:
    scripts = read_package_scripts(app_dir / "package.json")
    if script not in scripts:
        if optional:
            print(f"Skipping {name}: package.json has no '{script}' script.", flush=True)
            return None
        raise RuntimeError(f"Missing required npm script '{script}' in {app_dir.relative_to(REPO_ROOT)}/package.json.")

    npm = require_executable("npm", windows_fallback="npm.cmd")
    return Step(name=name, command=[npm, "run", script], cwd=app_dir)


def backend_steps() -> list[Step]:
    backend_dir = REPO_ROOT / "backend"
    detect_build_tool(backend_dir)
    return [
        Step(name=f"Backend Java quality {index}", command=command, cwd=backend_dir)
        for index, command in enumerate(build_quality_commands(backend_dir), start=1)
    ]


def frontend_steps() -> list[Step]:
    frontend_dir = REPO_ROOT / "frontend"
    steps: list[Step] = []
    for name, script, optional in (
        ("Frontend lint", "lint", False),
        ("Frontend format check", "format:check", True),
        ("Frontend type check", "type-check", False),
        ("Frontend tests", "test:run", True),
    ):
        step = npm_script_step(name, frontend_dir, script, optional=optional)
        if step:
            steps.append(step)
    return steps


def demo_steps() -> list[Step]:
    demo_dir = REPO_ROOT / "demo"
    steps: list[Step] = []
    for name, script in (
        ("Demo lint", "lint"),
        ("Demo type check", "type-check"),
    ):
        step = npm_script_step(name, demo_dir, script)
        if step:
            steps.append(step)
    return steps


def run_steps(area: str, steps: list[Step]) -> None:
    for step in steps:
        rel_cwd = step.cwd.relative_to(REPO_ROOT)
        print(f"[{area}] Running {step.name}: {' '.join(step.command)} (cwd: {rel_cwd})", flush=True)
        result = run_cmd(step.command, cwd=step.cwd)
        if result.returncode != 0:
            raise RuntimeError(f"{step.name} failed with exit code {result.returncode}.")


def run_ci(areas: set[str]) -> None:
    builders = {
        "backend": backend_steps,
        "frontend": frontend_steps,
        "demo": demo_steps,
    }
    selected = {area: builders[area]() for area in sorted(areas)}
    if not selected:
        print("No backend/frontend/demo changes detected; skipping local CI.", flush=True)
        return

    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=len(selected)) as executor:
        future_to_area = {
            executor.submit(run_steps, area, steps): area
            for area, steps in selected.items()
        }
        for future in as_completed(future_to_area):
            area = future_to_area[future]
            try:
                future.result()
                print(f"[{area}] CI passed.", flush=True)
            except Exception as exc:
                failures.append(f"{area}: {exc}")

    if failures:
        raise RuntimeError("Local CI failed:\n" + "\n".join(f"- {failure}" for failure in failures))


def normalize_commit_message(explicit_message: str | None) -> str | None:
    if explicit_message is None:
        return None
    message = explicit_message.strip()
    return message or None


def stage_commit_push(message: str, push: bool) -> str:
    add = git("add", "-A")
    ensure_success(add, "Unable to stage changes.")

    staged = git("diff", "--cached", "--quiet")
    if staged.returncode == 0:
        raise RuntimeError("No staged changes remain after validation.")

    cached_stat = git("diff", "--cached", "--stat", capture=True)
    ensure_success(cached_stat, "Unable to inspect staged changes.")
    print("Staged changes:", flush=True)
    print(cached_stat.stdout.rstrip(), flush=True)
    print(f"Commit message: {message}", flush=True)

    commit = git("commit", "-m", message)
    ensure_success(commit, "Unable to create commit.")

    rev = git("rev-parse", "--short", "HEAD", capture=True)
    ensure_success(rev, "Unable to resolve commit hash.")
    commit_hash = rev.stdout.strip()

    if push:
        push_result = git("push")
        if push_result.returncode != 0:
            raise RuntimeError(f"Push failed. Commit {commit_hash} remains local.")
    return commit_hash


def main() -> int:
    parser = argparse.ArgumentParser(description="Run scoped local CI, then commit and push git changes.")
    parser.add_argument("-m", "--message", help="Commit message summarized by the AI from the actual git changes.")
    parser.add_argument("--no-push", action="store_true", help="Create the commit locally without pushing.")
    parser.add_argument("--checks-only", action="store_true", help="Run selected local CI checks without committing or pushing.")
    parser.add_argument("--dry-run", action="store_true", help="Inspect changes and selected checks without running CI or committing.")
    args = parser.parse_args()

    try:
        status = git_status_short()
        if not status:
            print("No git changes detected; nothing to push.")
            return 0

        print("Git status:")
        print(status)

        files = changed_files()
        if not files:
            raise RuntimeError("Git status has changes, but no changed files were detected.")

        areas = detect_areas(files)
        message = normalize_commit_message(args.message)
        checks = ", ".join(sorted(areas)) if areas else "none"
        print(f"Changed files: {len(files)}")
        print(f"Selected CI areas: {checks}")
        if message:
            print(f"Commit message: {message}")
        elif not args.dry_run and not args.checks_only:
            raise RuntimeError("Commit message is required. Generate it from the git diff and pass --message.")

        if args.dry_run:
            return 0

        run_ci(areas)
        if args.checks_only:
            print("Selected local CI checks passed; no commit or push performed.")
            return 0

        commit_hash = stage_commit_push(message, push=not args.no_push)
        action = "committed" if args.no_push else "committed and pushed"
        print(f"Changes {action}: {commit_hash}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
