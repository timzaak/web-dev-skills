from pathlib import Path


def _resolve_repo_root() -> Path:
    """Resolve the project root directory.

    Default: scripts/lib/paths.py -> parents[2] = project root
    Works when installed as project_root/scripts/lib/paths.py
    """
    return Path(__file__).resolve().parents[2]


REPO_ROOT = _resolve_repo_root()
SCRIPTS_DIR = Path(__file__).resolve().parents[1]  # scripts/ directory (sibling of lib/)
LOG_DIR = REPO_ROOT / "log"
RUNTIME_DIR = LOG_DIR / "runtime"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

