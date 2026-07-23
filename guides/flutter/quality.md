# Flutter 验收规范

Flutter accept 默认只读，按目标项目 lock、设计和实际代码输出证据。跨领域门禁见 `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md`。

## 门禁

### P0

- 适用的格式、生成、`flutter analyze`、单元/widget 测试通过。
- 重要用户用例有对应 integration 回归证据。
- Riverpod 技术线一致，无平行状态系统。
- View/data 职责、依赖方向和生成物符合项目事实。

### P1

- 原生 UI 有 Patrol/等价自动化证据。
- 主题、本地化、Semantics、平台适配符合改动范围。
- 关键测试使用稳定 finder；复用达到阈值时提取 Screen/helper。
- 构建或性能敏感改动具备对应证据。

### P2

- 错误、空、加载和边界状态覆盖可继续提升。
- 重复 helper、finder 或测试脚手架可收敛。

## Riverpod 检查

- 精确检索 `package:flutter_bloc/`、`package:provider/`、`package:get/`、`package:mobx/`，不要误判 `flutter_riverpod`。
- 异步业务状态使用 `AsyncValue`；不平行维护 loading/error 标志。
- 生成声明/API 与 `pubspec.lock` 主版本一致；生成物未手工维护。

## 判定与报告

- `REJECTED`：任一适用 P0 失败。
- `ACCEPTED_WITH_IMPROVEMENTS`：P0 通过，仍有 P1/P2。
- `ACCEPTED`：适用门禁全部通过。

报告至少包含 feature/phase/slot/item、命令与结果、版本/设备、测试分层、Riverpod 结论、最终状态和改进项。不得为通过而跳过断言、关闭 lint、放宽 finder 或使用真实延迟。

命令见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/validation.md`；测试策略见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/testing.md`。
