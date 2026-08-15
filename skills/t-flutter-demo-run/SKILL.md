---
name: t-flutter-demo-run
description: Run and repair one Android Patrol user-story demo file.
argument-hint: "<patrol_test/**/*_test.dart> [--device <android-id>] [--dart-define KEY=VALUE]"
allowed-tools: [Read, Glob, Grep, Bash, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, Agent]
---

# Flutter Demo Run

按 `${CLAUDE_PLUGIN_ROOT}/protocols/flutter-demo-run-repair-contract.md` 执行单文件 Android Patrol 演示。

- 参数必须是存在的 `patrol_test/**/*_test.dart`。
- 优先使用目标项目 `scripts/flutter-demo-test-runner.py`；缺少时回退 `${CLAUDE_PLUGIN_ROOT}/scripts/flutter-demo-test-runner.py`。
- 首次运行整文件；失败后调用 `flutter-demo-diagnose`，按建议分发修复、补测并重跑，最多六轮。
- 所有 Agent 调用遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`。
- 最后一行只输出 `${CLAUDE_PLUGIN_ROOT}/protocols/demo-result-contract.md` 定义的 `Result`。

