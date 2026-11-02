# pi 扩展测试指南

Vitest 只覆盖不依赖 pi 进程的纯逻辑；扩展能否被 pi 正确加载、工具能否被模型调用由运行时冒烟提供证据，两种证据不得互相冒充。仅在运行时冒烟难稳定覆盖重要规则或异常边界时新增 Vitest，并说明可观察回归及覆盖缺口。允许不新增局部测试，受影响的现有测试仍需定向验证。先确认项目现有 scripts、测试目录与依赖版本，再选择受影响范围。

## Vitest

- 测的对象：typebox schema 的边界与拒绝输入、`prepareArguments` 对旧参数的折叠、`execute` 内可剥离的纯函数（解析、截断、路径归一）、从 `getBranch()` 条目重建状态的函数、`tool_call` 门的判定函数。
- 把 `ExtensionAPI` / `ExtensionContext` 作为薄接口注入，用最小 fake 记录 `registerTool` / `on` 调用或返回固定 `sessionManager` 条目；不 mock 整个 pi 运行时，不复制 pi 内部类型。
- 不为“扩展能导出工厂”“工具已注册”写占位测试；不以 fake 证明事件顺序、并行工具调度、缓存前缀或 TUI 渲染。
- 命令形式 `npm run test:run -- <文件或 pattern>`，脚本名以项目 `package.json` 为准；通用原则按 [frontend testing](${CLAUDE_PLUGIN_ROOT}/guides/frontend/testing.md) 读取。

## 运行时冒烟（证据）

- 初始化的无 provider 加载诊断可用项目 `npm run smoke:pi`（由 `t-init --pi` 补齐），它使用真实资源加载器和隔离配置；只证明资源发现与加载，不能作为下述工具行为、生命周期或 UI 验证的通过证据。
- 加载诊断：`pi -e ./extensions/<name>.ts --mode json -p "<最小触发提示>"`，或在 TUI 启动后查看启动诊断。扩展加载错误、skill 告警、工具注册失败必须为零。没有 provider 鉴权时只能验证加载与注册，证据中标注“未验证模型调用”。
- 工具行为：用 `--mode json` 的事件流核对 `tool_execution_start` / `tool_execution_end` 中的工具名、参数与结果，或在 TUI 用 `/reload` 后直接触发；截断、`isError`、`terminate` 行为以事件流为证据。
- 命令与 UI：`/<command>` 在 TUI 验证；RPC 模式下的 UI 行为按 pi 文档的 RPC Extension UI 核对；不在 print 模式下验证 UI。
- 包形态：优先在隔离的测试 cwd 和 agent 配置目录用 `pi -e ./<package>` 临时加载，确认清单资源（extensions、skills、prompts、themes）与过滤规则；只有验证安装流程时才在隔离配置中用 `pi install`，不改用户日常 settings。项目级资源按正常 project trust 流程验证，不静默放宽信任。
- 证据记录遵循 [验证证据契约](${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md)：冒烟命令、环境（pi 版本、provider、模式）与关键输出摘要写入 item Validation 或验收报告，不写成“通过”二字。

## 开发循环

- 扩展放在自动发现位置（`.pi/extensions/` 或包清单路径）用 `/reload` 热载；`pi -e` 只用于临时试验。
- 修改 skill、prompt、theme 后同样 `/reload`；资源发现问题看启动诊断与 `/skill:<name>` 是否出现。
- skill 的行为验证按 [skill-testing](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-testing.md)，在隔离临时目录进行并清理。
