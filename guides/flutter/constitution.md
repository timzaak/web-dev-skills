# Riverpod 技术线

Riverpod 是 Flutter 目标的唯一跨 widget/页面/生命周期状态线。纯局部 UI 状态可用 `StatefulWidget` + `setState`；禁止并行引入 Bloc、Provider、GetX、MobX、Service Locator 或 EventBus 状态系统。

## 版本与生成

- 先读 `pubspec.yaml`、`pubspec.lock`。
- `flutter_riverpod` 是运行时核心。
- `riverpod_annotation`、`riverpod_generator`、`build_runner` 均为可选。
- 项目已使用代码生成时可统一采用注解；不要仅为 Riverpod 引入生成器。
- 生成物不手工编辑；声明变化后按项目脚本刷新。

## Provider 选择

按是否暴露修改方法及初始化/返回值形态选择：

| 状态形态 | 声明式读取/派生，不暴露修改方法 | 需要暴露修改状态的方法 |
| --- | --- | --- |
| 同步值 | `Provider` | `NotifierProvider` |
| Future / FutureOr 异步初始化 | `FutureProvider` | `AsyncNotifierProvider` |
| Stream | `StreamProvider` | `StreamNotifierProvider` |

声明式读取也会随依赖、刷新或流事件更新。仅刷新用 `ref.invalidate` / `ref.refresh`，不必创建 Notifier；生成式声明由函数/类及返回类型推导。

表单输入、动画、controller 和路由选中态留在局部作用域；业务草稿确需跨页面共享时再提升归属。

## 读取、事件与生命周期

- `ref.watch` 订阅，事件中 `ref.read`，状态响应副作用用 `ref.listen`；异步状态用 `AsyncValue`，不重复维护 loading/error。
- Widget `build()` 不做 IO；provider 初始化可读数据，提交/删除由显式事件触发，避免重算重复写入。
- 参数化 provider 优先自动释放；保留缓存需说明失效条件。生成式默认自动释放，手写按 lock 版本配置；`keepAlive` 不等于持久化。
- `ref.onDispose` 清理自身资源，不修改其他 provider；依赖重算也会销毁旧状态，不受自动释放开关影响。

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

## 官方依据

相关规则有疑问时核对 [Providers](https://riverpod.dev/docs/concepts2/providers)、[DO/DON'T](https://riverpod.dev/docs/root/do_dont)、[Automatic disposal](https://riverpod.dev/docs/concepts2/auto_dispose)、[Code generation](https://riverpod.dev/docs/concepts/about_code_generation)（2026-09-25 核对 Riverpod 3.x；执行以项目 lock 为准）。
