# Flutter 验收规范

Flutter accept 默认只读，按目标项目 lock、设计和实际代码输出证据。公共结论、分级、报告和只读边界按验收前必须读取的 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`。跨领域检查见 `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md`。行为验证责任、阶段承接和证据复用按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。

## 门禁

### 必要门禁

- 适用的格式、生成、`flutter analyze`、单元/widget 测试通过。
- 本阶段负责的重要用户用例有场景/integration/Demo 或适用设备验证证据；后续 Demo 承接按验证证据协议，不重复要求多层覆盖。
- Riverpod 技术线一致，无平行状态系统。
- View/data 职责、依赖方向和生成物符合项目事实。

### 按变更范围适用的专项门禁

- 本阶段负责的原生 UI 行为有 Patrol/等价运行证据；真实后续 Demo 承接按验证证据协议。
- 主题、本地化、Semantics、平台适配符合改动范围。
- 关键测试使用稳定 finder；重复 Screen/helper 的整理按公共协议作为维护性检查，不设机械提取门禁。
- 构建或性能敏感改动具备对应证据。

### 维护性检查

- 非必要场景的错误、空、加载和边界状态覆盖可继续提升；本轮必要行为缺陷仍按公共协议阻断。
- 重复 helper、finder 或测试脚手架可收敛。

## Riverpod 检查

- 精确检索 `package:flutter_bloc/`、`package:provider/`、`package:get/`、`package:mobx/`，不要误判 `flutter_riverpod`。
- 异步业务状态使用 `AsyncValue`；不平行维护 loading/error 标志。
- 生成声明/API 与 `pubspec.lock` 主版本一致；生成物未手工维护。

## 判定与报告

结论、问题分级、报告路径和结构化返回只按公共验收协议；专项门禁缺失必要证据时不降级为维护性建议。

报告至少包含 feature/phase/slot/item、命令与结果、版本/设备、测试分层、Riverpod 结论、最终状态和改进项。不得为通过而跳过断言、关闭 lint、放宽 finder 或使用真实延迟。

命令见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/validation.md`；测试策略见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/testing.md`。
