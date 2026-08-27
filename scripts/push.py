#!/usr/bin/env python
import argparse
import hashlib
import json
import shlex
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from lib.cli import require_executable, run_cmd
from lib.paths import REPO_ROOT


@dataclass(frozen=True)
class Step:
    name: str
    command: list[str]
    cwd: Path


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


def git_private_path(path: str) -> Path:
    result = git("rev-parse", "--git-path", path, capture=True)
    ensure_success(result, f"Unable to resolve git private path: {path}")
    resolved = Path(result.stdout.strip())
    if not resolved.is_absolute():
        resolved = REPO_ROOT / resolved
    return resolved


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


def ci_cache_path(session: str) -> Path:
    return git_private_path(f"t-tools-push-ci/{session}.json")


def load_ci_cache(session: str) -> dict[str, dict[str, str]]:
    path = ci_cache_path(session)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_ci_cache(session: str, cache: dict[str, dict[str, str]]) -> None:
    path = ci_cache_path(session)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_ci_session(session: str) -> str:
    normalized = session.strip()
    if not normalized:
        raise RuntimeError("--ci-session is required.")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if any(char not in allowed for char in normalized):
        raise RuntimeError("--ci-session may only contain letters, digits, '.', '_' and '-'.")
    return normalized


def area_fingerprint(area: str) -> str:
    pathspec = f"{area}/"
    head = git("rev-parse", "HEAD", capture=True)
    ensure_success(head, "Unable to resolve HEAD.")
    diff = git("diff", "--binary", "HEAD", "--", pathspec, capture=True)
    ensure_success(diff, f"Unable to inspect {area} diff.")
    untracked = git("ls-files", "--others", "--exclude-standard", "-z", "--", pathspec, capture=True)
    ensure_success(untracked, f"Unable to inspect untracked {area} files.")

    digest = hashlib.sha256()
    digest.update(f"area:{area}\0".encode("utf-8"))
    digest.update(f"head:{head.stdout.strip()}\0".encode("utf-8"))
    digest.update(diff.stdout.encode("utf-8", errors="surrogateescape"))
    digest.update(untracked.stdout.encode("utf-8", errors="surrogateescape"))

    for path in split_z_output(untracked.stdout):
        normalized = path.replace("\\", "/")
        digest.update(f"\0untracked:{normalized}\0".encode("utf-8"))
        file_path = REPO_ROOT / path
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def read_package_scripts(package_json: Path) -> dict[str, str]:
    if not package_json.is_file():
        raise RuntimeError(f"Missing package.json: {package_json.relative_to(REPO_ROOT)}")
    data = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {str(key): str(value) for key, value in scripts.items()}


def npm_script_command(name: str, app_dir: Path, script: str) -> Step:
    npm = require_executable("npm", windows_fallback="npm.cmd")
    return Step(name=name, command=[npm, "run", script], cwd=app_dir)


def npm_script_step(name: str, app_dir: Path, script: str, *, optional: bool = False) -> Step | None:
    scripts = read_package_scripts(app_dir / "package.json")
    if script not in scripts:
        if optional:
            print(f"Skipping {name}: package.json has no '{script}' script.", flush=True)
            return None
        raise RuntimeError(f"Missing required npm script '{script}' in {app_dir.relative_to(REPO_ROOT)}/package.json.")

    return npm_script_command(name, app_dir, script)


def is_format_check_command(command: str) -> bool:
    normalized = " ".join(command.lower().split())
    return "--check" in normalized or "prettier -c" in normalized


def prettier_write_step_from_check(name: str, app_dir: Path, command: str) -> Step | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if not tokens or Path(tokens[0]).name not in {"prettier", "prettier.cmd"}:
        return None

    args = [token for token in tokens[1:] if token not in {"--check", "-c"}]
    npm = require_executable("npm", windows_fallback="npm.cmd")
    return Step(name=name, command=[npm, "exec", "prettier", "--", "--write", *args], cwd=app_dir)


def npm_format_fix_step(name: str, app_dir: Path, *, optional: bool = False) -> Step | None:
    scripts = read_package_scripts(app_dir / "package.json")
    for script in ("format:write", "format:fix", "format"):
        command = scripts.get(script)
        if command is None:
            continue
        if is_format_check_command(command):
            continue
        return npm_script_command(name, app_dir, script)

    check_command = scripts.get("format:check")
    if check_command:
        step = prettier_write_step_from_check(name, app_dir, check_command)
        if step:
            return step

    if optional:
        print(
            f"Skipping {name}: package.json has no writable format script "
            "('format:write', 'format:fix', non-check 'format', or Prettier 'format:check').",
            flush=True,
        )
        return None
    raise RuntimeError(
        f"Missing writable npm format script in {app_dir.relative_to(REPO_ROOT)}/package.json "
        "('format:write', 'format:fix', non-check 'format', or Prettier 'format:check')."
    )


def backend_steps() -> list[Step]:
    backend_dir = REPO_ROOT / "backend"
    if not (backend_dir / "Cargo.toml").is_file():
        raise RuntimeError("Backend changes detected, but backend/Cargo.toml was not found.")
    cargo = require_executable("cargo")
    return [
        Step(
            name="Backend clippy fix",
            command=[
                cargo,
                "clippy",
                "--fix",
                "--allow-dirty",
                "--allow-staged",
                "--all-targets",
                "--all-features",
                "--",
                "-D",
                "warnings",
            ],
            cwd=backend_dir,
        ),
        Step(name="Backend format", command=[cargo, "fmt", "--all"], cwd=backend_dir),
        # `cargo clippy --fix` exits 0 even when it cannot auto-resolve a denied
        # lint (it emits a warning instead), so a clean non-fixing check is needed
        # to actually enforce `-D warnings` and surface unfixable lints as failures.
        Step(
            name="Backend clippy check",
            command=[
                cargo,
                "clippy",
                "--all-targets",
                "--all-features",
                "--",
                "-D",
                "warnings",
            ],
            cwd=backend_dir,
        ),
    ]


def frontend_steps() -> list[Step]:
    frontend_dir = REPO_ROOT / "frontend"
    steps: list[Step] = []
    format_fix = npm_format_fix_step("Frontend format fix", frontend_dir, optional=True)
    if format_fix:
        steps.append(format_fix)
    for name, script, optional in (
        ("Frontend format check", "format:check", True),
        ("Frontend lint", "lint", False),
        ("Frontend type check", "type-check", False),
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


def run_ci(areas: set[str], *, ci_session: str, force_checks: bool = False) -> None:
    builders = {
        "backend": backend_steps,
        "frontend": frontend_steps,
        "demo": demo_steps,
    }
    cache = {} if force_checks else load_ci_cache(ci_session)
    selected: dict[str, list[Step]] = {}
    for area in sorted(areas):
        fingerprint = area_fingerprint(area)
        entry = cache.get(area)
        if entry and entry.get("status") == "passed" and entry.get("fingerprint") == fingerprint:
            print(f"[{area}] Skipping CI: unchanged since last successful run in session {ci_session}.", flush=True)
            continue
        selected[area] = builders[area]()

    if not selected:
        if areas:
            print("All selected CI areas are unchanged since their last successful run in this t-push session.", flush=True)
        else:
            print("No backend/frontend/demo changes detected; skipping local CI.", flush=True)
        return

    failures: list[str] = []
    passed: list[str] = []
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
                passed.append(area)
            except Exception as exc:
                failures.append(f"{area}: {exc}")

    if passed:
        for area in passed:
            cache[area] = {
                "status": "passed",
                "fingerprint": area_fingerprint(area),
            }
        save_ci_cache(ci_session, cache)

    if failures:
        raise RuntimeError("Local CI failed:\n" + "\n".join(f"- {failure}" for failure in failures))


def normalize_commit_message(explicit_message: str | None) -> str | None:
    if explicit_message is None:
        return None
    message = explicit_message.strip()
    return message or None


def stage_commit_push(message: str) -> str:
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

    push_result = git("push")
    if push_result.returncode != 0:
        raise RuntimeError(f"Push failed. Commit {commit_hash} remains local.")
    return commit_hash


def main() -> int:
    parser = argparse.ArgumentParser(description="Run scoped local CI, then commit and push git changes.")
    parser.add_argument("-m", "--message", required=True, help="Commit message summarized by the AI from the actual git changes.")
    parser.add_argument("--ci-session", required=True, help="Fresh id for this t-push execution; reuse only for its retries.")
    parser.add_argument("--force-checks", action="store_true", help="Ignore cached successful area checks and rerun selected local CI.")
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
        if message is None:
            raise RuntimeError("Commit message is required.")
        ci_session = normalize_ci_session(args.ci_session)
        checks = ", ".join(sorted(areas)) if areas else "none"
        print(f"Changed files: {len(files)}")
        print(f"Selected CI areas: {checks}")
        print(f"CI session: {ci_session}")
        print(f"Commit message: {message}")

        run_ci(areas, ci_session=ci_session, force_checks=args.force_checks)
        commit_hash = stage_commit_push(message)
        print(f"Changes committed and pushed: {commit_hash}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
