#!/usr/bin/env python3
"""Run one Android Patrol user-story demo and emit a stable Result line."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from lib.paths import REPO_ROOT


SECRET_KEY_RE = re.compile(r"(?:password|secret|token|key|credential)", re.IGNORECASE)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Android Patrol user-story demo runner")
    parser.add_argument("test_file", help="A patrol_test/**/*_test.dart file")
    parser.add_argument("--device", default="", help="Android device id")
    parser.add_argument("--run-id", default="", help="Stable run id")
    parser.add_argument("--dart-define", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--no-auto-env", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    return parser


def _run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        **kwargs,
    )


def validate_project(root: Path, test_file: str) -> Path:
    pubspec = root / "pubspec.yaml"
    lockfile = root / "pubspec.lock"
    if not pubspec.is_file() or not lockfile.is_file():
        raise ValueError("Flutter Demo requires pubspec.yaml and pubspec.lock")
    if not re.search(r"^\s*patrol:\s*(?:$|\S)", pubspec.read_text(encoding="utf-8"), re.MULTILINE):
        raise ValueError("pubspec.yaml does not declare Patrol")

    candidate = Path(test_file)
    target = (candidate if candidate.is_absolute() else root / candidate).resolve()
    patrol_root = (root / "patrol_test").resolve()
    try:
        target.relative_to(patrol_root)
    except ValueError as exc:
        raise ValueError("Flutter Demo target must be inside patrol_test/") from exc
    if not target.is_file() or not target.name.endswith("_test.dart"):
        raise ValueError(f"Patrol test file not found or invalid: {target}")
    return target


def android_devices(root: Path) -> list[dict[str, object]]:
    result = _run(["flutter", "devices", "--machine"], cwd=root, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "flutter devices --machine failed")
    try:
        devices = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("flutter devices returned invalid JSON") from exc
    return [
        device
        for device in devices
        if isinstance(device, dict)
        and str(device.get("targetPlatform", "")).lower().startswith("android")
        and bool(device.get("isSupported", True))
    ]


def select_android_device(root: Path, requested: str) -> str:
    devices = android_devices(root)
    if requested:
        if any(str(device.get("id")) == requested for device in devices):
            return requested
        raise ValueError(f"Requested device is not a supported Android device: {requested}")
    if len(devices) == 1:
        return str(devices[0]["id"])
    if not devices:
        raise ValueError("No supported Android device found; start/connect one and pass --device")
    ids = ", ".join(str(device.get("id")) for device in devices)
    raise ValueError(f"Multiple Android devices found ({ids}); pass --device")


def validate_dart_defines(values: list[str]) -> list[str]:
    for value in values:
        key, separator, _ = value.partition("=")
        if not separator or not key.strip():
            raise ValueError(f"Invalid --dart-define, expected KEY=VALUE: {value}")
    return values


def masked_define(value: str) -> str:
    key, _, raw = value.partition("=")
    return f"{key}=***" if SECRET_KEY_RE.search(key) else f"{key}={raw}"


def lifecycle_scripts(root: Path) -> tuple[Path | None, Path | None]:
    start = root / "scripts" / "flutter-demo-start.py"
    stop = root / "scripts" / "flutter-demo-stop.py"
    if start.exists() != stop.exists():
        raise ValueError(
            "Flutter Demo environment scripts must be provided as a pair: "
            "scripts/flutter-demo-start.py and scripts/flutter-demo-stop.py"
        )
    return (start if start.exists() else None, stop if stop.exists() else None)


def run_lifecycle(script: Path, root: Path) -> None:
    uv = shutil.which("uv")
    command = [uv, "run", str(script.relative_to(root))] if uv else [sys.executable, str(script)]
    result = _run(command, cwd=root, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or result.stderr.strip() or f"{script.name} failed")


def prepare_log_dir(root: Path, run_id: str) -> Path:
    log_dir = root / "patrol_test" / "test-results" / "runs" / run_id
    if log_dir.exists():
        shutil.rmtree(log_dir)
    log_dir.mkdir(parents=True)
    return log_dir


def emit_result(*, success: bool, exit_code: int, test_file: str, run_id: str,
                logs: str, duration: float, device: str, error: str = "") -> None:
    payload = {
        "success": "true" if success else "false",
        "fixed": "false",
        "logs": logs.replace("\\", "/"),
        "exitCode": exit_code,
        "testFile": test_file.replace("\\", "/"),
        "runId": run_id,
        "duration": duration,
        "device": device,
        "platform": "android",
        "error": error,
    }
    print(f"Result: {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = REPO_ROOT
    run_id = args.run_id or f"flutter-demo-{time.strftime('%Y%m%d-%H%M%S')}"
    started = time.monotonic()
    device = ""
    relative_test = args.test_file.replace("\\", "/")
    logs = f"patrol_test/test-results/runs/{run_id}"
    try:
        target = validate_project(root, args.test_file)
        defines = validate_dart_defines(args.dart_define)
        patrol = shutil.which("patrol")
        if not patrol:
            raise RuntimeError("patrol CLI not found; install a version compatible with pubspec.lock")
        doctor = _run([patrol, "doctor"], cwd=root, capture_output=True)
        if doctor.returncode != 0:
            raise RuntimeError(doctor.stdout.strip() or doctor.stderr.strip() or "patrol doctor failed")
        device = select_android_device(root, args.device)
        start_script, stop_script = lifecycle_scripts(root)
        auto_environment = not args.no_auto_env and start_script is not None
        try:
            if auto_environment:
                run_lifecycle(start_script, root)

            log_dir = prepare_log_dir(root, run_id)
            output_log = log_dir / "patrol-output.log"
            command = [patrol, "test", "--target", target.relative_to(root).as_posix(), "--device", device]
            for define in defines:
                command.extend(["--dart-define", define])
            print("Running: " + " ".join(
                masked_define(part) if "=" in part and part in defines else part for part in command
            ))
            try:
                with output_log.open("w", encoding="utf-8") as output:
                    process = subprocess.run(
                        command,
                        cwd=root,
                        stdout=output,
                        stderr=subprocess.STDOUT,
                        timeout=args.timeout,
                        check=False,
                    )
                exit_code = process.returncode
                error = "" if exit_code == 0 else "Patrol test failed; inspect patrol-output.log"
            except subprocess.TimeoutExpired:
                exit_code = 124
                error = f"Patrol test timed out after {args.timeout}s"
        finally:
            if auto_environment and stop_script:
                run_lifecycle(stop_script, root)
        duration = round(time.monotonic() - started, 1)
        emit_result(success=exit_code == 0, exit_code=exit_code, test_file=relative_test,
                    run_id=run_id, logs=logs, duration=duration, device=device, error=error)
        return exit_code
    except (OSError, RuntimeError, ValueError) as exc:
        duration = round(time.monotonic() - started, 1)
        emit_result(success=False, exit_code=2, test_file=relative_test, run_id=run_id,
                    logs=logs, duration=duration, device=device, error=str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
