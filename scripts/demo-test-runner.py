#!/usr/bin/env python
"""
Demo 测试运行器 - 集成环境管理。

自动检查并在必要时启动 Demo 环境，简化测试执行流程。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from lib.cli import require_executable
from lib.logger import Logger, LogLevel
from lib.paths import REPO_ROOT
from lib import demo_env


def escape_regex_pattern(pattern: str) -> str:
    """转义正则表达式中的特殊字符，使其字面匹配。"""
    # 需要转义的特殊字符：. ^ $ * + ? { } [ ] \ | ( )
    special_chars = r'.^$*+?{}[]\|()'
    return re.escape(pattern)


def normalize_legacy_args(argv: list[str]) -> list[str]:
    """转换旧版参数格式。"""
    mapping = {
        "-Mode": "--mode",
        "-LogLevel": "--log-level",
        "-RunId": "--run-id",
        "-Grep": "--grep",
        "-NoDedup": "--no-dedup",
        "-NoAggregate": "--no-aggregate",
        "-VerboseLog": "--verbose-log",
        "-QuietMode": "--quiet-mode",
        "-ListTests": "--list-tests",
    }
    return [mapping.get(arg, arg) for arg in argv]


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Demo test runner with integrated environment management"
    )
    parser.add_argument("test_file", nargs="?", default="", help="Test file or directory")
    parser.add_argument(
        "--mode",
        default="fast",
        choices=["fast", "full"],
        help="Test mode (default: fast)",
    )
    parser.add_argument(
        "--log-level", default="", help="Log level: verbose, mini (default: mini)"
    )
    parser.add_argument("--run-id", default="", help="Run ID for logging")
    parser.add_argument("--grep", default="", help="Filter tests by pattern")
    parser.add_argument("--no-dedup", action="store_true", help="Disable log deduplication")
    parser.add_argument("--no-aggregate", action="store_true", help="Disable log aggregation")
    parser.add_argument("--verbose-log", action="store_true", help="Verbose log output")
    parser.add_argument("--quiet-mode", action="store_true", help="Quiet mode (minimal output)")
    parser.add_argument("--list-tests", action="store_true", help="List tests without running")
    parser.add_argument("--compact", action="store_true", help="Compact log format")
    parser.add_argument(
        "--no-auto-env",
        action="store_true",
        help="Do not auto-manage environment (assume it's already running)",
    )
    return parser


def ensure_environment(
    auto_manage: bool = True, require_frontend: bool = True
) -> bool:
    """确保 Demo 环境运行且健康。

    Args:
        auto_manage: 是否自动管理环境（启动/停止）
        require_frontend: 是否要求前端必须启动

    Returns:
        环境健康返回 True，否则返回 False
    """
    if not auto_manage:
        return True

    # 检查环境状态
    status = demo_env.check_environment_health(require_frontend=require_frontend)

    if status.healthy:
        return True

    print('[demo-test-runner] Demo environment is not healthy; rebuilding environment...')

    # 环境不健康，启动新环境
    logger = Logger(LogLevel.NORMAL)
    return demo_env.start_environment(logger=logger, timeout=120)


def run_tests(
    test_file: str,
    mode: str,
    log_level: str,
    run_id: str | None,
    grep: str,
    no_dedup: bool,
    no_aggregate: bool,
    verbose_log: bool,
    quiet_mode: bool,
    list_tests: bool,
    compact: bool,
) -> int:
    """运行 Playwright 测试。

    Args:
        test_file: 测试文件路径
        mode: 测试模式
        log_level: 日志级别
        run_id: 运行 ID
        grep: 测试过滤模式
        no_dedup: 禁用日志去重
        no_aggregate: 禁用日志聚合
        verbose_log: 详细日志
        quiet_mode: 静默模式
        list_tests: 仅列出测试
        compact: 紧凑格式

    Returns:
        退出码（0 表示成功）
    """
    demo_dir = REPO_ROOT / "demo"
    if not demo_dir.exists():
        print(f"Error: demo directory not found at: {demo_dir}")
        return 1

    if not test_file:
        print("Usage: uv run scripts/demo-test-runner.py [test-file] [options]")
        return 1

    # 规范化测试文件路径
    # Playwright testDir is './e2e', so we need path relative to that
    # Input can be: 'demo/e2e/regular-user/test.e2e.ts' or 'e2e/regular-user/test.e2e.ts'
    # Output should be: 'regular-user/test.e2e.ts'
    test_file = test_file.replace("\\", "/")

    # Remove 'demo/' prefix if present
    if test_file.startswith("demo/"):
        test_file = test_file[5:]  # Remove 'demo/'

    # Remove 'e2e/' prefix if present (since testDir is './e2e')
    if test_file.startswith("e2e/"):
        test_file = test_file[4:]  # Remove 'e2e/'

    # 确定日志级别
    if verbose_log:
        log_level = "verbose"
    elif quiet_mode:
        log_level = "mini"
    if not log_level:
        log_level = "mini"

    # 切换到 demo 目录
    os.chdir(demo_dir)

    # 清理旧的测试结果
    for old in ("test-results/artifacts", "test-results/runs", "playwright-report"):
        path = Path(old)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    # 创建日志目录
    run_id = run_id or f"run-{time.strftime('%Y%m%d-%H%M%S')}"
    log_dir = Path("test-results/runs") / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    playwright_log = log_dir / "playwright-output.log"

    # 转换为绝对路径用于清晰输出
    abs_playwright_log = playwright_log.resolve()
    # 设置环境变量
    env = dict(os.environ)
    env["DEMO_LOG_LEVEL"] = log_level
    env["DEMO_LOG_DEDUP"] = "false" if no_dedup else "true"
    env["DEMO_LOG_AGGREGATE"] = "false" if no_aggregate else "true"
    env["DEMO_RUN_ID"] = run_id
    env["DEMO_LOG_COMPACT"] = "true" if compact else "false"
    env["DEBUG"] = env.get("DEBUG", "pw:api")

    # 构建 Playwright 命令
    npx = require_executable("npx", windows_fallback="npx.cmd")
    cmd = [npx, "playwright", "test", test_file, "--project=demo-fast"]
    if grep:
        # 转义正则表达式特殊字符，使其字面匹配
        escaped_grep = escape_regex_pattern(grep)
        cmd.append(f"--grep={escaped_grep}")
    if list_tests:
        cmd.append("--list")
        print(f"Listing tests in: {test_file}")
    else:
        cmd.append("--quiet")

    # 运行测试
    start = time.time()
    exit_code = -1
    with playwright_log.open("w", encoding="utf-8") as log_fp:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            log_fp.write(line)
            if list_tests:
                # Windows 控制台编码问题的安全输出处理
                try:
                    print(line, end="")
                except UnicodeEncodeError:
                    # 回退：替换有问题的字符
                    print(
                        line.encode("ascii", errors="replace").decode("ascii"), end=""
                    )
        exit_code = proc.wait()
    duration = round(time.time() - start, 1)

    # 生成摘要
    summary = {
        "success": "true" if exit_code == 0 else "false",
        "logs": str(log_dir).replace("\\", "/"),
        "exitCode": exit_code,
        "testFile": test_file,
        "mode": mode,
        "logLevel": log_level,
        "duration": duration,
        "runId": run_id,
        "grep": grep,
    }

    # 打印结果
    if not list_tests and exit_code != 0:
        try:
            print(f"✗ Failed ({exit_code})")
        except UnicodeEncodeError:
            print(f"[X] Failed ({exit_code})")
        unified_logs_dir = (demo_dir / "test-results" / "unified-logs").resolve()
        service_log_dir = (REPO_ROOT / "log").resolve()
        print(f"  Playwright: {abs_playwright_log}")
        print(f"  Unified: {unified_logs_dir}/{run_id}-*")
        print(f"  Backend: {service_log_dir}/backend-demo.log.*")
        print(f"  Frontend: {service_log_dir}/frontend-demo.log.*")
    print(f"Result: {json.dumps(summary, ensure_ascii=False, separators=(',', ':'))}")

    return exit_code


def main() -> int:
    # 解析参数
    args = build_parser().parse_args(normalize_legacy_args(sys.argv[1:]))

    # 检查环境
    # --list-tests 不需要检查环境（快速列出测试用例）
    auto_manage = not args.no_auto_env and not args.list_tests
    require_frontend = not args.list_tests

    if auto_manage:
        if not ensure_environment(
            auto_manage=auto_manage, require_frontend=require_frontend
        ):
            print("ERROR: Failed to start/verify environment")
            return 1

    # 运行测试
    exit_code = run_tests(
        test_file=args.test_file,
        mode=args.mode,
        log_level=args.log_level,
        run_id=args.run_id,
        grep=args.grep,
        no_dedup=args.no_dedup,
        no_aggregate=args.no_aggregate,
        verbose_log=args.verbose_log,
        quiet_mode=args.quiet_mode,
        list_tests=args.list_tests,
        compact=args.compact,
    )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())


