from pathlib import Path
import os
import subprocess


def _resolve_repo_root() -> Path:
    """Resolve the project root directory.

    Priority:
    1. AI_PROJECT_ROOT override for intentional shared-script use
    2. git rev-parse --show-toplevel anchored to this scripts tree
    3. Walk this scripts tree upward for CLAUDE.md / .git marker
    4. parents[2] relative to this file
    """
    override = os.environ.get("CLAUDE_PROJECT_DIR")
    if override:
        return Path(override).expanduser().resolve()

    override = os.environ.get("AI_PROJECT_ROOT")
    if override:
        return Path(override).expanduser().resolve()

    script_project_root = Path(__file__).resolve().parents[2]

    # Try git detection from the scripts tree, not the caller's CWD.
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=script_project_root,
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            git_root = Path(result.stdout.strip()).resolve()
            if git_root.is_dir():
                return git_root
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Walk from the scripts tree upward for marker files.
    for parent in [script_project_root, *script_project_root.parents]:
        if (parent / "CLAUDE.md").is_file() or (parent / ".git").exists():
            return parent

    # Fallback: assume scripts are inside the project.
    return script_project_root


REPO_ROOT = _resolve_repo_root()
SCRIPTS_DIR = Path(__file__).resolve().parents[1]  # scripts/ directory (sibling of lib/)
LOG_DIR = REPO_ROOT / "log"
RUNTIME_DIR = LOG_DIR / "runtime"
TEST_CONFIG_DIR = RUNTIME_DIR / "test-config"
BACKEND_TEST_LOG = LOG_DIR / "backend-test-output.log"
PGDOG_TEST_CONFIG = TEST_CONFIG_DIR / "pgdog-test.toml"
PGDOG_USERS_CONFIG = TEST_CONFIG_DIR / "users-test.toml"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
