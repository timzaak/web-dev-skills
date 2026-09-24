---
name: t-flutter-demo-accept
description: Accept Android Patrol demos against their user stories and execution evidence.
argument-hint: "<file|domain|all> [--device <android-id>]"
allowed-tools: [Read, Glob, Grep, Bash, Write]
---

# Flutter Demo Accept

按目标解析 `patrol_test/**/*_test.dart`，并遵循 `${CLAUDE_PLUGIN_ROOT}/agents/flutter-demo-accept.md`：

- 强制检查用户故事路径/US ID、场景覆盖和关键断言。
- 按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 核查 `dart analyze <test-file>` 和相关整文件 `flutter-demo-test-runner.py` Android 门禁证据；有效结果可复用，缺失或失效才补跑。
- 检查真实 App 入口、环境/数据清理、finder、等待和日志证据。
- 输出 `.ai/quality/flutter-demo-accept-*.md`；任一 MANDATORY 门禁失败即 `REJECTED`。

