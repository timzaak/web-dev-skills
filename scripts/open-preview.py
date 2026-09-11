#!/usr/bin/env python3
"""Open an HTML Preview and report a delivery verification level.

Levels (mirrors protocols/html-show-contract.md 「送达验证分级」):
- verified-tab:     macOS only. Opened with Chrome, window activated, and the
                    active tab URL read back matching the file:// URL.
- verified-command: Open command exited 0. Visibility NOT confirmed.
- none:             Open command failed; nothing may be claimed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

CHROME_READBACK = """
tell application "Google Chrome"
  activate
  set active tab index of front window to (count tabs of front window)
  return URL of active tab of front window
end tell
"""

READBACK_WAIT_SECONDS = 1.5


def _normalize(url: str) -> str:
    return url.rstrip("/").replace("file://localhost/", "file:///").lower()


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True)


def _readback_url(file_url: str) -> tuple[str | None, str]:
    """Best-effort readback of the Chrome active tab URL. Returns (url, note)."""
    try:
        proc = _run(["osascript", "-e", CHROME_READBACK])
    except FileNotFoundError:
        return None, "osascript 不可用"
    if proc.returncode != 0:
        reason = (proc.stderr or "").strip().splitlines()
        return None, f"读回失败: {reason[0] if reason else '未知错误'}"
    url = proc.stdout.strip()
    if _normalize(url) == _normalize(file_url):
        return url, "活动 tab URL 与 file:// 一致"
    return url, f"活动 tab URL 不匹配: {url}"


def open_preview(path: Path) -> dict:
    result = {
        "path": str(path),
        "file_url": path.resolve().as_uri(),
        "command": "",
        "verification": "none",
        "status": "failed",
        "evidence": "",
    }

    if not path.is_file():
        result["evidence"] = "Preview 文件不存在"
        return result

    if sys.platform == "darwin":
        chrome = _run(["open", "-a", "Google Chrome", str(path)])
        if chrome.returncode == 0:
            result["command"] = f'open -a "Google Chrome" "{path}"'
            time.sleep(READBACK_WAIT_SECONDS)
            url, note = _readback_url(result["file_url"])
            if url is not None and _normalize(url) == _normalize(result["file_url"]):
                result["verification"] = "verified-tab"
                result["status"] = "opened"
                result["evidence"] = note
            else:
                result["verification"] = "verified-command"
                result["status"] = "open-command-executed"
                result["evidence"] = note
        else:
            fallback = _run(["open", str(path)])
            result["command"] = f'open "{path}"'
            result["verification"] = "verified-command" if fallback.returncode == 0 else "none"
            result["status"] = "open-command-executed" if fallback.returncode == 0 else "failed"
            result["evidence"] = "Chrome 打开失败，已用默认浏览器打开" if fallback.returncode == 0 else (fallback.stderr or "open 失败").strip()
    elif sys.platform == "win32":
        win_path = str(path.resolve())
        proc = _run(["cmd.exe", "/c", "start", "", win_path])
        result["command"] = f'cmd.exe /c start "" "{win_path}"'
        if proc.returncode == 0:
            result["verification"] = "verified-command"
            result["status"] = "open-command-executed"
            result["evidence"] = "退出码 0；当前平台无无工具的 tab 读回手段，可见性未确认"
        else:
            result["evidence"] = (proc.stderr or "start 失败").strip()
    else:
        proc = _run(["xdg-open", str(path)])
        result["command"] = f'xdg-open "{path}"'
        if proc.returncode == 0:
            result["verification"] = "verified-command"
            result["status"] = "open-command-executed"
            result["evidence"] = "退出码 0；当前平台无无工具的 tab 读回手段，可见性未确认"
        else:
            result["evidence"] = (proc.stderr or "xdg-open 失败").strip()

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Open an HTML Preview and report delivery verification.")
    parser.add_argument("path", help="Preview HTML file path")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    result = open_preview(Path(args.path))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"open-preview: {result['status']} ({result['verification']})")
        print(f"  command: {result['command']}")
        print(f"  evidence: {result['evidence']}")

    return 0 if result["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
