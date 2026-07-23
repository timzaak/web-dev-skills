# Flutter 规范入口

flutter 规范入口，按"先定位问题，再读对应页面"使用。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| 当前 flutter 架构事实、`lib/` 目录职责、路由与主题约束 | [development.md](${CLAUDE_PLUGIN_ROOT}/guides/flutter/development.md) |
| Riverpod 状态管理技术线约束真相 | [constitution.md](${CLAUDE_PLUGIN_ROOT}/guides/flutter/constitution.md) |
| Widget 组合、Riverpod 消费、异步、表单、路由的高频模式 | [patterns.md](${CLAUDE_PLUGIN_ROOT}/guides/flutter/patterns.md) |
| 单元测试与 widget 测试 how-to、测试边界 | [testing.md](${CLAUDE_PLUGIN_ROOT}/guides/flutter/testing.md) |
| 演示测试：integration_test、真机/模拟器、Patrol 原生交互、selector 策略 | [integration-testing.md](${CLAUDE_PLUGIN_ROOT}/guides/flutter/integration-testing.md) |
| 完成前最小验证命令与门禁 | [validation.md](${CLAUDE_PLUGIN_ROOT}/guides/flutter/validation.md) |
| 只读验收、Riverpod 线一致性、测试分层与 Demo 门禁 | [quality.md](${CLAUDE_PLUGIN_ROOT}/guides/flutter/quality.md) |

## 使用规则

- `development.md` 是 flutter 的事实型主规范，其他页面不应重复定义第二套架构真相。
- `constitution.md` 是状态管理技术线约束真相，agent 文档只引用不重写。
- `testing.md` 只负责单元/widget 测试 how-to，不负责演示测试；演示测试看 `integration-testing.md`。
- `integration-testing.md` 是 demo-first 测试策略在 flutter 上的载体，独立成页是因为 selector 策略、Screen Object、设备与原生交互足够复杂。
- agent 文档只定义执行顺序、门禁和输出契约，不重新发明框架、路由、状态管理或测试规范。

## 官方核对基线

本规范最近按以下官方资料核对（2026-07-14）：

- Flutter 3.44.0 文档：[Architecture recommendations](https://docs.flutter.dev/app-architecture/recommendations)、[Testing overview](https://docs.flutter.dev/testing/overview)、[Integration tests](https://docs.flutter.dev/testing/integration-tests)、[Performance best practices](https://docs.flutter.dev/perf/best-practices)
- flutter_riverpod 3.3.2（当前稳定包）与 Riverpod 3.x 文档：[Provider containers](https://riverpod.dev/docs/concepts2/containers)、[About code generation](https://riverpod.dev/docs/concepts/about_code_generation)
- go_router 17.3.0 当前稳定包：[go_router on pub.dev](https://pub.dev/packages/go_router)
- Patrol 4.6.1 当前稳定包与 4.x 文档：[Install Patrol](https://patrol.leancode.co/documentation)、[Native automation usage](https://patrol.leancode.co/documentation/native/usage)

这些版本只表示插件规范的核对基线。执行目标项目任务时，仍以目标项目 `pubspec.lock` 和对应版本官方文档为准。
