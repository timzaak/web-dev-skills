# Riverpod 技术线

Riverpod 是 Flutter 目标的唯一跨 widget/页面/生命周期状态线。纯局部 UI 状态可用 `StatefulWidget` + `setState`；禁止并行引入 Bloc、Provider、GetX、MobX、Service Locator 或 EventBus 状态系统。

## 版本与生成

- 先读 `pubspec.yaml`、`pubspec.lock`。
- `flutter_riverpod` 是运行时核心。
- `riverpod_annotation`、`riverpod_generator`、`build_runner` 均为可选。
- 项目已使用代码生成时可统一采用注解；不要仅为 Riverpod 引入生成器。
- 生成物不手工编辑；声明变化后按项目脚本刷新。

## Provider 选择

- 可变同步业务状态：`NotifierProvider`。
- 可变异步业务状态：`AsyncNotifierProvider` + `AsyncValue`。
- 只读派生值/依赖注入：`Provider`。
- 声明式异步读取：`FutureProvider`；流式订阅：`StreamProvider`。

使用 `ref.watch` 订阅，事件中用 `ref.read`；副作用放事件回调或 `ref.listen`，不放 `build()`。异步状态不要再平行维护 loading/error 标志。

## 组织

- provider 随 feature 放置；跨 feature 基础设施放 `lib/core/`。
- 命名表达领域语义，不表达 API 实现细节。
- 延续项目现有目录与声明风格，不为单个修改机械迁移全库。
- 不把不相关状态塞进同一 Notifier/provider 文件。

## 测试与诊断

- Widget/integration 测试通过 `ProviderScope(overrides: [...])` 注入 fake。
- 单元测试通过 container 读取 provider；Notifier 使用 `container.read(xxxProvider.notifier)`。
- Riverpod 3 使用 `ProviderContainer.test()`；override API 必须匹配 lock 版本。
- `flutter analyze` 验证类型/lint；精确检索禁用 package；`git diff` + 生成器验证派生文件。analyze 本身不能证明生成物未被手改。

测试示例见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/testing.md`，消费示例见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/patterns.md`。
