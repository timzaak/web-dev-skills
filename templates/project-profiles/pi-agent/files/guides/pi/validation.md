# pi 完成前验证

先从实际项目确认包管理器、scripts 与可用工具；本地命令选择和发布同步规则按 [pi 项目协议](${CLAUDE_PLUGIN_ROOT}/protocols/pi-project-contract.md)。有 pi 专项类型检查脚本时优先使用（初始化可补 `type-check:pi`），否则使用覆盖实际 pi 源码的项目检查；无脚本时用项目已安装的 TypeScript 配合 `tsconfig.json` 执行 `--noEmit`。不得借 `npx` 联网安装工具，也不得用运行时冒烟替代必要的类型检查。

| 检查 | 何时执行 | 成功证据 |
|---|---|---|
| 类型检查 | JS/TS 实现、类型或影响代码的依赖/TS 配置变更 | 项目脚本或本地编译器 `--noEmit` 退出码为 0；缺配置或工具为未完成 |
| 定向测试 | 受影响逻辑有测试、补测或任务要求 | 相关 Vitest 通过；缺失必要测试不能视为通过 |
| 加载诊断 | 扩展、skill、prompt、theme 或清单变更 | 按 [testing.md](${CLAUDE_PLUGIN_ROOT}/guides/pi/testing.md) 运行时冒烟：无扩展加载错误与资源告警，新注册的工具、命令、skill 可见 |
| 清单与依赖核对 | `package.json` 或资源路径变更 | `pi` 清单路径可解析；host 包只在 `peerDependencies`；新增运行时依赖在 `dependencies` 且为精确版本 |
| 行为冒烟 | 工具、命令、事件钩子或状态逻辑变更 | 事件流或 TUI 证据显示预期工具名、参数与结果；需要 provider 时标注鉴权状态 |
| lint | 项目已有该门禁 | 使用不改写源码的检查模式 |

在包根分别运行，例如 `npm run type-check`、`npm run test:run -- <相关文件>`、`pi -e ./extensions/<name>.ts --mode json -p "<提示>"`。仅文档或 skill 文本变更可跳过类型检查并说明原因，skill 行为按 [skill-testing](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-testing.md) 验证。

实现 agent 修复失败项后重跑受影响检查，最多重试 3 次；仍失败时返回失败原因、证据和可恢复动作，不标记完成。accept 不修代码，按 [公共验收协议](${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md) 返回判定，由编排层停止并交回对应实现/测试 item。

验收允许运行冒烟和写质量报告，但不改源码、依赖声明、lockfile 或 settings，不运行 autofix。缺少必需脚本或 pi 不可用时报告门禁未完成，不临时安装工具或静默略过。
