# Flutter 开发、Riverpod 与常用模式规范

目标项目代码、`pubspec.yaml`、`pubspec.lock`、`analysis_options.yaml` 是版本、目录和依赖真相；本页定义稳定架构边界、Riverpod 状态技术线与高频实现模式。测试见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/testing.md`，验证与验收见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/quality.md`。

## 1. 技术、架构与目录

默认倾向 Flutter stable、Material 3、go_router、Riverpod、dio、freezed/json_serializable；项目事实优先。旧项目渐进收敛，不做无收益重写。

- **UI**：View 负责渲染、布局、动画和简单导航；需要公开状态修改操作时，由适用的 Notifier 承担 ViewModel 等价职责；只读数据可直接消费声明式 provider。
- **Data**：Repository 是一类应用数据的真相来源；Service 封装 HTTP、存储和平台插件。
- **Domain**：仅在复杂或重复业务逻辑挤占多个 Notifier 时引入。
- **依赖方向与数据流**：`View -> provider/Notifier -> Repository -> Service`（provider 负责依赖注入）；事件向下、状态向上；模型优先不可变，View 不直接修改数据源。
- **目录骨架**（先识别现有结构再沿用）：`lib/main.dart` / `lib/app.dart`（启动与根装配）、`lib/core/`（跨 feature 基础设施）、`lib/features/<domain>/`（页面/widget/provider/model）、`lib/router/`（路由表与守卫）。
- **API 客户端与生成物**：已有 API client 生成流程时优先复用生成物；契约变化后先再生客户端再调业务层，不手工编辑任何生成文件；未采用生成器的项目不强制引入。

## 2. Riverpod 状态技术线

Riverpod 是 Flutter 目标的唯一跨 widget/页面/生命周期状态线。纯局部 UI 状态可用 `StatefulWidget` + `setState`；禁止并行引入 Bloc、Provider、GetX、MobX、Service Locator 或 EventBus 状态系统。

- 先读 `pubspec.yaml`、`pubspec.lock`：`flutter_riverpod` 是运行时核心；`riverpod_annotation` / `riverpod_generator` / `build_runner` 均为可选，项目已使用代码生成时可统一采用注解，不要仅为 Riverpod 引入生成器。
- Provider 选型：

| 状态形态 | 声明式读取/派生，不暴露修改方法 | 需要暴露修改状态的方法 |
| --- | --- | --- |
| 同步值 | `Provider` | `NotifierProvider` |
| Future / FutureOr 异步初始化 | `FutureProvider` | `AsyncNotifierProvider` |
| Stream | `StreamProvider` | `StreamNotifierProvider` |

- 仅刷新用 `ref.invalidate` / `ref.refresh`，不必创建 Notifier；生成式声明由函数/类及返回类型推导。
- 表单输入、动画、controller 和路由选中态留在局部作用域；业务草稿确需跨页面共享时再提升归属。
- `ref.watch` 订阅，事件中 `ref.read`，状态响应副作用用事件回调/`ref.listen`；异步状态用 `AsyncValue`，不重复维护 loading/error，用户错误映射为本地化消息。
- Widget `build()` 不做 IO、副作用或昂贵重复计算；provider 初始化可读数据，提交/删除由显式事件触发，避免重算重复写入。
- 参数化 provider 优先自动释放；保留缓存需说明失效条件（`keepAlive` 不等于持久化）；`ref.onDispose` 清理自身资源，不修改其他 provider；依赖重算也会销毁旧状态。
- 组织：provider 随 feature 放置，跨 feature 基础设施放 `lib/core/`；命名表达领域语义，不把不相关状态塞进同一文件；延续项目现有风格，不为单个修改机械迁移全库。
- 测试与诊断要点：Widget/integration 测试通过 `ProviderScope(overrides: [...])` 注入 fake；单测用 container（Riverpod 3 用 `ProviderContainer.test()`）与 `container.read(xxxProvider.notifier)`；`flutter analyze` + 精确检索禁用 package + `git diff` 校验派生文件。

## 3. UI、平台与恢复边界

- 设计值走 `ThemeData`、`ColorScheme`、`ThemeExtension`；用可用空间而非设备型号做响应式布局，覆盖目标平台键鼠、焦点和触摸输入；用户文案走本地化；自定义交互补齐 Semantics 与可访问名称；大列表惰性构建。
- 性能结论来自 profile mode、DevTools/时间线或 performance test，不凭 debug 观感猜测。
- 平台代码、权限和通道仅在必要时修改并写入 Handoff；复用插件/channel 封装，明确调用、错误及不支持平台的行为；权限申请覆盖拒绝/撤销及从系统设置返回后的重检。
- 区分页面释放、前后台切换与进程重建，明确操作取消/恢复及资源清理；[生命周期通知可能跳过](https://api.flutter.dev/flutter/dart-ui/AppLifecycleState.html)，不依赖退出回调做唯一持久化；[Android 状态恢复](https://docs.flutter.dev/platform-integration/android/restore-state-android) 不等于业务数据持久化；离线写入需同步、幂等、冲突处理与反馈。

## 4. 常用实现模式

先复用目标项目现有 widget、provider 和 helper；以下示例只表达规则：

- **Widget**：优先 `StatelessWidget` 与 `const`；按职责和状态变化边界拆分，不设机械行数门槛。
- **Riverpod 消费与代码生成示例**：

```dart
final users = ref.watch(userListProvider);
return users.when(
  data: (items) => UserList(items: items),
  loading: () => const CircularProgressIndicator(),
  error: (_, _) => Text(context.l10n.loadFailed),
);

@riverpod
Future<List<User>> userSearch(Ref ref, String keyword) {
  return ref.watch(userRepositoryProvider).search(keyword);
}
```

重试按钮的事件回调使用 `ref.invalidate(userSearchProvider(keyword))`；需要等待刷新完成的交互使用 `ref.refresh(userSearchProvider(keyword).future)`。

- **表单**：校验用 `FormField.validator`，文案本地化、样式主题化，提交/loading/error 状态集中管理：

```dart
TextFormField(
  decoration: InputDecoration(labelText: context.l10n.emailLabel),
  validator: (value) {
    if (value == null || value.isEmpty) return context.l10n.emailRequired;
    return value.contains('@') ? null : context.l10n.emailInvalid;
  },
)
```

- **路由**：复用项目当前 `go_router`/typed route；守卫集中处理，多导航栈使用 `ShellRoute`/`StatefulShellRoute`；认证状态必须能触发路由刷新，不引用作用域外的 `ref`，不无条件重建 `GoRouter`。

## 5. 官方核对基线

最近按以下官方资料核对（执行目标项目任务时仍以目标项目 `pubspec.lock` 与对应版本官方文档为准）：

- Flutter 3.44.0：[Architecture recommendations](https://docs.flutter.dev/app-architecture/recommendations)、[Testing overview](https://docs.flutter.dev/testing/overview)、[Integration tests](https://docs.flutter.dev/testing/integration-tests)、[Performance best practices](https://docs.flutter.dev/perf/best-practices)
- Riverpod 3.x（`flutter_riverpod 3.3.2`）：[Providers](https://riverpod.dev/docs/concepts2/providers)、[DO/DON'T](https://riverpod.dev/docs/root/do_dont)、[Automatic disposal](https://riverpod.dev/docs/concepts2/auto_dispose)、[Provider containers](https://riverpod.dev/docs/concepts2/containers)、[Code generation](https://riverpod.dev/docs/concepts/about_code_generation)
- `go_router 17.3.0`：[go_router on pub.dev](https://pub.dev/packages/go_router)
- Patrol 4.x：[Install Patrol](https://patrol.leancode.co/documentation)、[Compatibility table](https://patrol.leancode.co/documentation/compatibility-table)、[Develop](https://patrol.leancode.co/cli-commands)、[Build and test bundling](https://patrol.leancode.co/cli-commands/build)、[Native automation usage](https://patrol.leancode.co/documentation/native/usage)
