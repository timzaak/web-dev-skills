#!/usr/bin/env python
import argparse
import hashlib
import json
import os
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


def worktree_fingerprint() -> str:
    files = git("ls-files", "--cached", "--others", "--exclude-standard", "-z", capture=True)
    ensure_success(files, "Unable to snapshot the working tree.")
    digest = hashlib.sha256()
    for name in sorted(set(split_z_output(files.stdout))):
        if name.replace("\\", "/").startswith(".ai/"):
            continue
        path = REPO_ROOT / name
        if not path.exists() and not path.is_symlink():
            continue
        digest.update(name.encode("utf-8") + b"\0")
        if path.is_symlink():
            digest.update(b"symlink\0" + os.readlink(path).encode("utf-8"))
        elif path.is_file():
            digest.update(str(path.stat().st_mode & 0o111).encode("ascii") + b"\0")
            content = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    content.update(chunk)
            digest.update(content.digest())
        else:
            raise RuntimeError(f"Cannot snapshot non-file git entry: {name}")
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def push_record_path(session: str) -> Path:
    return git_private_path(f"t-tools-push-ci/{session}-push.json")


def save_push_record(session: str, record: dict) -> None:
    path = push_record_path(session)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_push_record(session: str) -> dict | None:
    path = push_record_path(session)
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid push recovery record: {path}") from exc
    if not isinstance(record, dict) or record.get("status") not in ("committing", "pending", "completed"):
        raise RuntimeError(f"Invalid push recovery record: {path}")
    for field in ("branch", "remote", "ref", "base_head", "message", "fingerprint"):
        if not isinstance(record.get(field), str) or not record[field]:
            raise RuntimeError(f"Invalid push recovery field: {field}")
    if record["status"] != "committing" and (not isinstance(record.get("commit"), str) or not record["commit"]):
        raise RuntimeError("Push recovery record is missing its commit.")
    return record


def current_head() -> str:
    result = git("rev-parse", "HEAD", capture=True)
    ensure_success(result, "Unable to resolve HEAD.")
    return result.stdout.strip()


def push_target() -> tuple[str, str, str]:
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD", capture=True)
    ensure_success(branch, "Push requires a branch, not detached HEAD.")
    name = branch.stdout.strip()
    remote = git("config", "--get", f"branch.{name}.remote", capture=True)
    ref = git("config", "--get", f"branch.{name}.merge", capture=True)
    ensure_success(remote, "Configure an upstream remote before pushing.")
    ensure_success(ref, "Configure an upstream branch before pushing.")
    if remote.stdout.strip() == "." or not ref.stdout.strip().startswith("refs/heads/"):
        raise RuntimeError("Push requires an external upstream branch.")
    return name, remote.stdout.strip(), ref.stdout.strip()


def remote_contains(record: dict) -> bool:
    result = git("ls-remote", "--exit-code", record["remote"], record["ref"], capture=True)
    if result.returncode == 2:
        return False
    ensure_success(result, "Unable to confirm the remote branch.")
    remote_head = result.stdout.split()[0]
    if remote_head == record["commit"]:
        return True
    fetched = git("fetch", "--no-tags", record["remote"], record["ref"], capture=True)
    ensure_success(fetched, "Unable to inspect the remote commit ancestry.")
    ancestor = git("merge-base", "--is-ancestor", record["commit"], "FETCH_HEAD", capture=True)
    if ancestor.returncode not in (0, 1):
        ensure_success(ancestor, "Unable to confirm remote commit ancestry.")
    return ancestor.returncode == 0


def finish_push(session: str, record: dict) -> str:
    if not remote_contains(record):
        result = git("push", record["remote"], f"{record['commit']}:{record['ref']}")
        ensure_success(result, f"Push failed. Commit {record['commit']} remains local; reuse CI session {session}.")
    if not remote_contains(record):
        raise RuntimeError(f"Remote has not confirmed commit {record['commit']}.")
    record["status"] = "completed"
    save_push_record(session, record)
    return record["commit"]


def resume_push(session: str, record: dict) -> str | None:
    if push_target() != (record["branch"], record["remote"], record["ref"]):
        raise RuntimeError("Push target changed; preserve the recovery record and resolve it before retrying.")
    head = current_head()
    if record["status"] == "committing":
        if head == record["base_head"]:
            return None
        parent = git("rev-parse", "HEAD^", capture=True)
        message = git("log", "-1", "--format=%B", capture=True)
        if parent.returncode != 0 or parent.stdout.strip() != record["base_head"] or message.stdout.strip() != record["message"]:
            raise RuntimeError("Cannot identify the interrupted commit; preserve the recovery record.")
        record.update(status="pending", commit=head)
        save_push_record(session, record)
    if head != record["commit"] or worktree_fingerprint() != record["fingerprint"] or any(not name.startswith(".ai/") for name in changed_files()):
        raise RuntimeError("Code changed after the recorded commit; revalidate it before starting a new push session.")
    return finish_push(session, record)


def stage_commit_push(message: str, *, ci_session: str, expected_fingerprint: str | None = None) -> str:
    branch, remote, ref = push_target()
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

    fingerprint = worktree_fingerprint()
    if expected_fingerprint is not None and fingerprint != expected_fingerprint:
        raise RuntimeError("Working tree changed after acceptance; revalidate before committing.")
    record = {
        "status": "committing", "branch": branch, "remote": remote, "ref": ref,
        "base_head": current_head(), "message": message, "fingerprint": fingerprint,
    }
    save_push_record(ci_session, record)

    commit = git("commit", "-m", message)
    ensure_success(commit, "Unable to create commit.")

    record.update(status="pending", commit=current_head())
    save_push_record(ci_session, record)
    if worktree_fingerprint() != fingerprint or any(not name.startswith(".ai/") for name in changed_files()):
        raise RuntimeError("Commit hooks changed the working tree; revalidate before pushing.")
    return finish_push(ci_session, record)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run scoped local CI, then commit and push git changes.")
    parser.add_argument("-m", "--message", help="Commit message summarized by the AI from the actual git changes.")
    parser.add_argument("--ci-session", required=True, help="Fresh id for this t-push execution; reuse only for its retries.")
    parser.add_argument("--force-checks", action="store_true", help="Ignore cached successful area checks and rerun selected local CI.")
    parser.add_argument("--check-only", action="store_true", help="Run local CI and print a worktree fingerprint without committing or pushing.")
    parser.add_argument("--expected-fingerprint", help="Require the accepted worktree fingerprint before and after CI, and before commit.")
    args = parser.parse_args(argv)

    try:
        ci_session = normalize_ci_session(args.ci_session)
        if args.expected_fingerprint is not None and worktree_fingerprint() != args.expected_fingerprint:
            raise RuntimeError("Working tree differs from the accepted fingerprint; revalidate before pushing.")
        if not args.check_only:
            record = load_push_record(ci_session)
            if record is not None:
                commit_hash = resume_push(ci_session, record)
                if commit_hash is not None:
                    print(f"Changes committed and pushed: {commit_hash}")
                    return 0
        status = git_status_short()
        if not status:
            if args.check_only:
                print(f"Validated worktree fingerprint: {worktree_fingerprint()}")
                return 0
            branch, remote, ref = push_target()
            record = {"status": "pending", "branch": branch, "remote": remote, "ref": ref,
                      "base_head": current_head(), "commit": current_head(),
                      "message": args.message or "Retry existing commit", "fingerprint": worktree_fingerprint()}
            save_push_record(ci_session, record)
            commit_hash = finish_push(ci_session, record)
            print(f"Existing commit confirmed on remote: {commit_hash}")
            return 0

        print("Git status:")
        print(status)

        files = changed_files()
        if not files:
            raise RuntimeError("Git status has changes, but no changed files were detected.")

        areas = detect_areas(files)
        message = normalize_commit_message(args.message)
        if message is None and not args.check_only:
            raise RuntimeError("Commit message is required.")
        checks = ", ".join(sorted(areas)) if areas else "none"
        print(f"Changed files: {len(files)}")
        print(f"Selected CI areas: {checks}")
        print(f"CI session: {ci_session}")
        print(f"Commit message: {message}")

        run_ci(areas, ci_session=ci_session, force_checks=args.force_checks)
        fingerprint = worktree_fingerprint()
        if args.expected_fingerprint is not None and fingerprint != args.expected_fingerprint:
            raise RuntimeError("Local CI modified the accepted code; revalidate before committing or pushing.")
        if args.check_only:
            print(f"Validated worktree fingerprint: {fingerprint}")
            return 0
        commit_hash = stage_commit_push(message, ci_session=ci_session, expected_fingerprint=args.expected_fingerprint)
        print(f"Changes committed and pushed: {commit_hash}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
