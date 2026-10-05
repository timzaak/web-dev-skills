# Flutter 验证步骤

先读目标项目脚本、`pubspec.yaml`、`pubspec.lock` 和 `analysis_options.yaml`；项目命令优先于下列默认值。

## 默认顺序

```bash
cd <flutter-dir>
dart format --set-exit-if-changed .

# 仅在生成声明源发生变化时
dart run build_runner build --delete-conflicting-outputs

flutter analyze
# 仅运行本次受影响的现有或新增局部测试；路径取自项目
flutter test test/<affected-path>
```

要求：格式无漂移、analyze 零 issue、受影响单元/widget 测试通过。无适用局部测试时不为运行命令补占位测试；业务验证责任及证据复用按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。生成器是可选能力；未采用的项目不运行 build_runner，不手工编辑生成物。

## 按范围追加

| 改动 | 验证 |
| --- | --- |
| 重要用户用例 | 复用适用 Demo 或定向 `flutter test integration_test/<file> -d <device-id>`；不重复覆盖，后续承接按验证证据协议 |
| Flutter Web integration | ChromeDriver + `flutter drive`，见 `integration-testing.md` |
| 原生 UI | `patrol test --target <file>` 或设计批准的等价方案 |
| manifest、平台代码、依赖或发版 | 对应 `flutter build apk/ios/web` |
| 自定义交互/关键页面 | `meetsGuideline` 测试，按需 TalkBack/VoiceOver |
| 滚动、动画、首屏、大列表 | profile mode + DevTools/时间线或 integration performance test |

## 失败处理

- 先重跑最小失败文件，再跑受影响集合；不默认升级全量。
- 不跳过断言、关闭 lint、添加真实延迟或手改生成物。
- integration 超时时先排查无限动画和同步条件。
- 设备型测试记录设备、OS、Flutter 与依赖锁定版本。
- 任一适用的 MANDATORY 门禁未过，不得标记完成。

测试分层见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/testing.md`；验收判定见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/quality.md`。
