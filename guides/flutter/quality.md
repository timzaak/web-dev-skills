# Flutter 验证与验收规范

先读目标项目脚本、`pubspec.yaml`、`pubspec.lock` 和 `analysis_options.yaml`；项目命令优先于下列默认值。公共验收结论、分级、报告和只读边界按 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`；跨领域检查见 `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md`；行为验证责任、阶段承接与证据复用按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。

## 1. 完成前验证步骤

### 默认顺序

```bash
cd <flutter-dir>
dart format --set-exit-if-changed .

# 仅在生成声明源发生变化时
dart run build_runner build --delete-conflicting-outputs

flutter analyze
# 仅运行本次受影响的现有或新增局部测试；路径取自项目
flutter test test/<affected-path>
```

要求：格式无漂移、analyze 零 issue、受影响单元/widget 测试通过。无适用局部测试时不为运行命令补占位测试；生成器是可选能力，未采用的项目不运行 `build_runner`，不手工编辑生成物。

### 按范围追加验证

| 改动 | 验证 |
| --- | --- |
| 重要用户用例 | 复用适用 Demo 或定向 `flutter test integration_test/<file> -d <device-id>`；不重复覆盖，后续承接按验证证据协议 |
| Flutter Web integration | ChromeDriver + `flutter drive`，见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/testing.md` |
| 原生 UI | `patrol test --target <file>` 或设计批准的等价方案 |
| manifest、平台代码、依赖或发版 | 对应 `flutter build apk/ios/web` |
| 自定义交互/关键页面 | `meetsGuideline` 测试，按需 TalkBack/VoiceOver |
| 滚动、动画、首屏、大列表 | profile mode + DevTools/时间线或 integration performance test |

失败处理：先重跑最小失败文件再跑受影响集合，不默认升级全量；不跳过断言、关闭 lint、添加真实延迟或手改生成物；integration 超时先排查无限动画和同步条件；设备型测试记录设备、OS、Flutter 与依赖锁定版本；任一适用的 MANDATORY 门禁未过不得标记完成。

## 2. 只读验收规范（flutter-accept）

### 必要门禁

- 适用的格式、生成、`flutter analyze`、单元/widget 测试通过。
- 本阶段负责的重要用户用例有场景/integration/Demo 或适用设备验证证据；后续 Demo 承接按验证证据协议，不重复要求多层覆盖。
- Riverpod 技术线一致，无平行状态系统：精确检索 `package:flutter_bloc/`、`package:provider/`、`package:get/`、`package:mobx/`（勿误判 `flutter_riverpod`）；异步业务状态用 `AsyncValue`；生成声明/API 与 `pubspec.lock` 主版本一致且生成物未被手工维护。
- View/data 职责、依赖方向和生成物符合项目事实。

### 按变更范围适用的专项门禁与维护性检查

- 本阶段负责的原生 UI 行为有 Patrol/等价运行证据；主题、本地化、Semantics、平台适配符合改动范围；关键测试使用稳定 finder；构建或性能敏感改动具备对应证据。
- 维护性改进（不自动阻断）：非必要场景的错误/空/加载边界补充、重复 Screen/helper/finder 收敛。

### 判定与报告

结论、问题分级、报告路径和结构化返回只按公共验收协议；专项门禁缺失必要证据时不降级为维护性建议。报告至少包含 feature/phase/slot/item、命令与结果、版本/设备、测试分层、Riverpod 结论、最终状态和改进项。
