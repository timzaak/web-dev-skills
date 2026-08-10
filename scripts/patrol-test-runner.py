#!/usr/bin/env python3
"""Run selected Patrol files in one build, with an optional isolated-file mode.

The default uses repeated ``--target`` arguments in a single ``patrol test``
invocation so Patrol can bundle the tests and build the app once. Use
``--isolate-files`` only when per-file continuation and summaries are more
valuable than execution speed.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from lib.paths import REPO_ROOT


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
SUMMARY_RE = re.compile(
    r"Total:\s*(\d+).*?Successful:\s*(\d+).*?Failed:\s*(\d+).*?Skipped:\s*(\d+)",
    re.DOTALL,
)
DURATION_RE = re.compile(r"Duration:\s*([^\r\n]+)")


@dataclass(frozen=True)
class Device:
    id: str
    name: str
    platform: str
    is_emulator: bool


@dataclass(frozen=True)
class TestResult:
    target: str
    exit_code: int
    total: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    duration: str = ""

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


def patrol_test_directory(root: Path) -> Path:
    pubspec = root / "pubspec.yaml"
    if not pubspec.is_file():
        raise ValueError("pubspec.yaml not found")
    lines = pubspec.read_text(encoding="utf-8").splitlines()
    in_patrol = False
    for line in lines:
        if re.match(r"^patrol:\s*(?:#.*)?$", line):
            in_patrol = True
            continue
        if not in_patrol:
            continue
        if line and not line[0].isspace() and not line.lstrip().startswith("#"):
            break
        match = re.match(r"^\s+test_directory:\s*['\"]?([^'\"#\s]+)", line)
        if match:
            return (root / match.group(1)).resolve()
    return (root / "patrol_test").resolve()


def discover_tests(root: Path) -> list[Path]:
    test_dir = patrol_test_directory(root)
    if not test_dir.is_dir():
        return []
    return sorted(
        path
        for path in test_dir.rglob("*_test.dart")
        if "test-results" not in path.parts and path.name != "test_bundle.dart"
    )


def expand_targets(root: Path, raw_targets: list[str]) -> list[Path]:
    if not raw_targets:
        return discover_tests(root)
    expanded: list[Path] = []
    seen: set[Path] = set()
    for raw in raw_targets:
        for value in raw.split(","):
            value = value.strip()
            if not value:
                continue
            candidate = (root / value).resolve()
            matches = (
                sorted(candidate.rglob("*_test.dart"))
                if candidate.is_dir()
                else [candidate]
            )
            for path in matches:
                if not path.is_file() or not path.name.endswith("_test.dart"):
                    raise ValueError(f"Patrol target not found or invalid: {value}")
                if "test-results" in path.parts or path.name == "test_bundle.dart":
                    continue
                if path not in seen:
                    seen.add(path)
                    expanded.append(path)
    return expanded


def flutter_devices(root: Path) -> list[Device]:
    result = subprocess.run(
        ["flutter", "devices", "--machine"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "flutter devices --machine failed")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("flutter devices returned invalid JSON") from exc
    return [
        Device(
            id=str(item.get("id", "")),
            name=str(item.get("name", "")),
            platform=str(item.get("targetPlatform") or item.get("platform") or ""),
            is_emulator=bool(item.get("emulator", False)),
        )
        for item in payload
        if isinstance(item, dict) and bool(item.get("isSupported", True))
    ]


def select_device(devices: list[Device], platform: str, requested: str) -> Device:
    marker = "android" if platform == "android" else "ios"
    candidates = [device for device in devices if marker in device.platform.lower()]
    if requested:
        for device in candidates:
            if requested in {device.id, device.name}:
                return device
        raise ValueError(f"Requested device is not a supported {platform} device: {requested}")
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise ValueError(f"No supported {platform} device found")
    values = ", ".join(device.id for device in candidates)
    raise ValueError(f"Multiple {platform} devices found ({values}); pass --device")


def resolve_mode(requested: str, device: Device) -> str:
    physical_ios = "ios" in device.platform.lower() and not device.is_emulator
    if physical_ios:
        return "release"
    return requested


def parse_result(target: str, exit_code: int, output: str) -> TestResult:
    plain = ANSI_RE.sub("", output)
    match = SUMMARY_RE.search(plain)
    values = tuple(int(value) for value in match.groups()) if match else (0, 0, 0, 0)
    duration_match = DURATION_RE.search(plain)
    return TestResult(
        target=target,
        exit_code=exit_code,
        total=values[0],
        successful=values[1],
        failed=values[2],
        skipped=values[3],
        duration=duration_match.group(1).strip() if duration_match else "",
    )


def run_patrol(command: list[str], root: Path, label: str) -> TestResult:
    print(f"Running: {' '.join(command)}", flush=True)
    process = subprocess.Popen(
        command,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        lines.append(line)
    process.wait()
    return parse_result(label, process.returncode, "".join(lines))


def build_command(
    patrol: str,
    device: Device,
    mode: str,
    targets: list[Path],
    root: Path,
    extra: list[str],
) -> list[str]:
    command = [patrol, "test", "--device", device.id]
    if mode:
        command.append(f"--{mode}")
    for target in targets:
        command.extend(["--target", target.relative_to(root).as_posix()])
    command.extend(extra)
    return command


def print_summary(results: list[TestResult]) -> None:
    print("\nPatrol summary")
    print("Status  Passed/Total  Duration  Target")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{status:<7} {result.successful}/{result.total:<12} "
            f"{result.duration:<9} {result.target}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Patrol tests with one bundled build by default")
    parser.add_argument("-t", "--target", action="append", default=[])
    parser.add_argument("-d", "--device", default="")
    parser.add_argument("--platform", choices=["android", "ios"], default="android")
    parser.add_argument("--isolate-files", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--debug", action="store_const", const="debug", dest="mode")
    mode.add_argument("--profile", action="store_const", const="profile", dest="mode")
    mode.add_argument("--release", action="store_const", const="release", dest="mode")
    parser.add_argument("patrol_args", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = REPO_ROOT
    try:
        patrol = shutil.which("patrol")
        if not patrol:
            raise RuntimeError("patrol CLI not found; install a version compatible with pubspec.lock")
        targets = expand_targets(root, args.target)
        if not targets:
            raise ValueError("No Patrol *_test.dart files found")
        device = select_device(flutter_devices(root), args.platform, args.device)
        mode = resolve_mode(args.mode or "", device)
        extra = args.patrol_args[1:] if args.patrol_args[:1] == ["--"] else args.patrol_args

        relative_targets = [path.relative_to(root).as_posix() for path in targets]
        print(
            f"Device: {device.name} ({device.id}), platform={args.platform}, "
            f"mode={mode or 'default'}, files={len(targets)}"
        )
        if args.isolate_files:
            results = [
                run_patrol(
                    build_command(patrol, device, mode, [target], root, extra),
                    root,
                    target.relative_to(root).as_posix(),
                )
                for target in targets
            ]
        else:
            results = [
                run_patrol(
                    build_command(patrol, device, mode, targets, root, extra),
                    root,
                    ",".join(relative_targets),
                )
            ]
        print_summary(results)
        return 0 if all(result.passed for result in results) else 1
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Patrol runner error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

