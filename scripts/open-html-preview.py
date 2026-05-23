#!/usr/bin/env python3
"""Open a generated PRD HTML Preview in the default browser."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import webbrowser
from pathlib import Path


def open_path(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=True)
        return
    try:
        subprocess.run(["xdg-open", str(path)], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        webbrowser.open(path.as_uri())


def main() -> int:
    parser = argparse.ArgumentParser(description="Open a PRD HTML Preview.")
    parser.add_argument("preview", help="Path to .ai/preview/<domain>/<feature>.html")
    parser.add_argument("--root", default=".", help="Target project root, defaults to current directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    preview = (root / args.preview).resolve()
    try:
        preview.relative_to(root)
    except ValueError:
        print(f"Preview path is outside project root: {preview}", file=sys.stderr)
        return 2

    if preview.suffix.lower() != ".html":
        print(f"Preview path is not an HTML file: {preview}", file=sys.stderr)
        return 2
    if not preview.exists():
        print(f"Preview file does not exist: {preview}", file=sys.stderr)
        return 1

    open_path(preview)
    print(f"Opened PRD HTML Preview: {preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
