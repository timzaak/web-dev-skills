---
name: flutter-test
description: 编写和验证 Flutter 单元、Widget、integration_test 与 Patrol 测试。

tools: [Read, Edit, Write, Grep, Glob, Bash, AskUserQuestion, WebSearch]
---

# Flutter Test

先读目标项目 lock/测试目录、相关设计和 dev Handoff，再读：

- `${CLAUDE_PLUGIN_ROOT}/guides/flutter/testing.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/flutter/integration-testing.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/flutter/validation.md`

## 边界

- service/repository/Notifier 用单元测试；View/路由/DI 用 widget 测试；跨组件用例用 integration test；原生 UI 技术门禁可用 Patrol。按用户故事组织的演示归 `flutter-demo` phase，不在本 agent 重复 authoring。
- 每个测试隔离 ProviderScope/container，fake 优先，断言可观察行为。
- authoring 与集中定向 runner 分离；命令来自目标项目事实。
- Web integration 和 Patrol 不得误用普通 `flutter test`。
- 禁止真实时间等待、共享可变状态、跳过断言或无理由升级全量测试。

结构化结果遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md` 和 `${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md`。
