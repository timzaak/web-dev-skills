# pi 扩展开发规范

先读目标项目已有的 `package.json`（`pi` 清单、`keywords`、`peerDependencies`、scripts）、`.pi/settings.json`、资源与设计，确认 pi 版本（`pi --version`）、运行模式和受影响资源。项目识别、首次交付及包与项目级资源的区分按 [pi 项目协议](${CLAUDE_PLUGIN_ROOT}/protocols/pi-project-contract.md)；已有项目沿用实际位置，不为纯 skill 资源强建 Node 工程。

## 技术基线

- Node.js 22.19+ 与 TypeScript；pi 通过 jiti 直接加载 `.ts`，不引入独立构建产物，类型检查用项目脚本或已有本地编译器 `--noEmit`。
- 扩展类型与 helper 从 `@earendil-works/pi-coding-agent` 导入；参数 schema 用 `typebox`，字符串枚举用 `@earendil-works/pi-ai` 的 `StringEnum`；TUI 组件用 `@earendil-works/pi-tui`。这些 host 包只在 `peerDependencies` 声明 `"*"`，不得进入 `dependencies`，不得打包；旧名 `@mariozechner/*`、`@sinclair/typebox` 映射到同一模块，新代码不使用旧名。
- 扩展自身的运行时依赖写入 `dependencies` 并锁精确版本；`devDependencies` 在 `pi install` 时不安装。
- 测试选择与配置见 [testing.md](${CLAUDE_PLUGIN_ROOT}/guides/pi/testing.md)。

## 清单与资源发现

- `package.json` 的 `pi` 字段声明 `extensions` / `skills` / `prompts` / `themes`，值为相对包根的路径或 glob 数组；没有清单时 pi 从约定目录自动发现。dot 前缀或 symlink 资源根不会被 glob 遍历到，必须显式列出。
- `keywords` 含 `pi-package` 才会进入 pi.dev 包目录（gallery）发现，不影响本地资源加载；`pi.changelogPath` 指向变更记录。
- 项目级资源 `.pi/extensions/`、`.pi/skills/`、`.pi/settings.json` 只在 project trust 后加载。拼接项目配置路径用 `CONFIG_DIR_NAME`，不硬编码 `.pi`；读取项目级扩展配置前核对 `ctx.isProjectTrusted()`。
- 扩展发现一层深：单文件 `*.ts`、目录 `index.ts`，或带 `pi.extensions` 的 `package.json`；更大的包通过清单声明入口。

## 扩展工厂与生命周期

- 扩展默认导出 `(pi: ExtensionAPI) => void | Promise<void>`；异步工厂在 `session_start`、`resources_discover` 与 provider 注册刷新之前完成。
- 工厂可能在不启动会话的调用中执行：不在工厂启动进程、socket、watcher 或定时器，延迟到 `session_start` 或真正需要的命令/工具，并注册幂等的 `session_shutdown` 清理。
- `/new`、`/resume`、`/fork`、`/reload` 会销毁并重建扩展实例：内存态在 `session_shutdown` 清理、在 `session_start` 重建。`withSession` 回调只使用传入的新 ctx，不复用旧 `pi`、旧 `ctx` 或提前取出的 `sessionManager`。
- `registerTool` / `registerCommand` 在加载期或 `session_start` 之后都可调用，新工具立即生效；`registerProvider` 在工厂内排队、工厂外立即生效；MCP 注册不持久化，每次加载重新注册。

## 事件与钩子

- 一次 prompt 的生命周期：`input` → `before_agent_start` → `agent_start` → turns → `agent_end` → 可能的重试/压缩/队列消息 → `agent_before_settle` → `agent_settled`。`agent_end` 不是空闲信号，“已停止”语义用 `agent_settled`。
- `turn_end` / `agent_before_settle` 返回 `continue: true` 必须带守卫条件，否则下一次响应后再次评估会形成死循环。
- 工具调用钩子顺序：`tool_execution_start` → `tool_call`（可阻断/改参）→ `tool_execution_update` → `tool_result`（可改结果）→ `tool_execution_end`；观察全部终态只用 `tool_execution_end`。`tool_call` 作安全门时无法判定即阻断（fail closed），返回 `{ block: true, reason }`。
- 修改系统提示优先改 `before_agent_start` 的 `systemPromptOptions.sections` / `selectedTools` / `promptGuidelines`（pi 只追加差异、保留缓存前缀）；返回 `systemPrompt` 或设置 `forceSystemPrompt` 会整体替换并导致缓存失效，只在设计明确要求时使用。
- `context` 只见非 system 消息，无法丢掉提示与工具声明；`context_with_system` 拥有完整 transcript，索引 0 必须保留 system message。
- 处理器按扩展加载顺序链式执行：转换类处理器保留不属于自己的字段；通知类处理器不在流式事件里做慢操作。

## 工具

- 定义 `name`、`label`、`description`、`parameters`（typebox）与 `execute(toolCallId, params, signal, onUpdate, ctx)`，返回 `{ content, details }`；`onUpdate` 的部分结果同样需要 `details`，同一工具的 `details` 类型保持一致。
- `promptSnippet` 提供一行描述；`promptGuidelines` 平铺追加且没有工具名前缀，每条必须点名工具（“Use my_tool when…”），不写“this tool”。
- 输出必须截断：内置上限 50KB 与 2000 行取先到者，用 `truncateHead`（文件、搜索结果）或 `truncateTail`（日志、命令输出）；截断时告知模型完整输出位置，并在工具描述中写明上限。
- 同一条 assistant 消息的工具调用默认并行。改文件的工具把整个读改写窗口包进 `withFileMutationQueue(absolutePath, fn)`，路径先解析为绝对路径；共享可变内存态的工具设 `executionMode: "sequential"`。
- 错误用抛错或 `isError: true`，需要同时携带数据时用后者；嵌套调用模型时返回 `usage`；`terminate: true` 只在本批全部终态结果都终止时跳过后续模型调用。
- 旧会话参数形状变化用 `prepareArguments` 折叠到当前 schema；公开 schema 保持严格，不为兼容增加废弃字段。
- `exposure` 取 `direct | model-only | codemode | deferred | hidden`；工具不可注销，撤回用 `hidden` 重注册。`annotations`（`readOnlyHint`、`destructiveHint` 等）供权限门判断，pi 不校验其真实性。
- `ctx.executeTool` 的嵌套调用不进入 transcript，由调用方通过 `onUpdate` 和 `details` 自行汇报。
- 覆盖内置工具（`read`、`bash`、`powershell`、`edit`、`write`、`grep`、`find`、`ls`）必须保持结果形状与 `details` 类型；未定义的渲染槽继承内置渲染，`promptSnippet` / `promptGuidelines` 不继承。
- 接受路径参数的工具归一化模型可能加上的 `@` 前缀。

## 状态与持久化

- 有状态工具把状态写入结果 `details`，在 `session_start` 与 `session_tree` 从 `ctx.sessionManager.getBranch()` 重建；不从全部 entries 重建，废弃分支是替代历史。
- 不进入模型上下文的持久数据用 `pi.appendEntry(customType, data)`，需要显示时配 `registerEntryRenderer`；需要进入模型上下文的用 `pi.sendMessage`。
- `pi.sendUserMessage` 在流式期间必须指定 `deliverAs`；需要触发命令或模板展开时显式传 `expandPromptTemplates: true`。

## 命令、快捷键与 UI

- `registerCommand` 处理器收到 `ExtensionCommandContext`；`newSession`、`fork`、`switchSession`、`navigateTree`、`reload`、`waitForIdle` 只在命令中调用，工具与事件处理器不得调用。
- `await ctx.reload()` 视为处理器终点，之后不再使用旧内存态。
- 对话类 UI（`select`、`confirm`、`input`、`editor`）与 `notify`、`setStatus`、`setWidget` 在 TUI 与 RPC 可用，调用前核对 `ctx.hasUI`；`ctx.ui.custom()`、组件工厂与终端输入只在 `ctx.mode === "tui"`。print / json 模式下 UI 方法为空操作，逻辑不得依赖其返回值。
- 渲染器返回 `Component`，默认 `Text` padding `(0, 0)`，处理 `isPartial` 与 `expanded`；键位提示用渲染上下文的 `keyHint` / `keyText`。

## Provider、MCP 与外部进程

- `pi.registerProvider` 注册或覆盖 provider；`apiKey` 支持 `$ENV`、`${ENV}` 与 `!command`。扩展内调用模型用 `ctx.modelRegistry.streamSimple` / `complete`，不用 `pi-ai/compat` 的直连函数（看不到扩展注册的 provider）。
- `pi.registerMcpServer(name, config)` 的 config 与 `mcp.json` 条目同形；同名 `mcp.json` 优先。`mcp.json` 与 `settings.json` 由用户维护，扩展不改写。
- 子进程用 `pi.exec(command, args, { signal, timeout, cwd })`，无 shell；可取消的工作传递 `ctx.signal`。

## Skills 与 prompt templates

- 随包分发的 skill 按 Agent Skills 规范编写；写作与行为验证遵循 [skill-authoring](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-authoring.md) 与 [skill-testing](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-testing.md)，本节只列 pi 差异。
- 发现位置：包清单 `skills`、`~/.pi/agent/skills/`、`.pi/skills/`、`~/.agents/skills/`、`.agents/skills/`，递归发现含 `SKILL.md` 的目录。显式触发为 `/skill:<name> [args]`；只允许显式触发的 skill 设 `disable-model-invocation: true`。
- 同名冲突保留先发现者并告警；缺 `description` 或 frontmatter 畸形不加载；`name` 不超过 64 字符，`description` 不超过 1024。
- 选型：固定提示用 prompt template（`/<name>` 展开）；需要更多上下文与附带脚本、但不需要新的可执行集成点用 skill；需要新工具、命令、事件拦截或 UI 用 extension。
- 修改资源后 `/reload`；自动发现位置可热载，`pi -e ./path.ts` 只用于临时试验。

## 安全与权限

- 扩展以 pi 进程的全部操作系统权限运行，可读取提示、工具调用、文件、凭据与会话；只加载可信来源，`.pi/` 资源在 project trust 后加载。
- pi 没有内置权限系统。设计要求的权限边界用 `tool_call` 门（按 `annotations` 或命令模式确认/阻断）或容器化（Gondolin、Docker、OpenShell）实现；不在扩展里静默放宽或绕过 project trust，安全决策无法判定时阻断。

## 打包与分发

- 包布局：`package.json`（`pi` 清单、`keywords: ["pi-package"]`、host 包在 `peerDependencies`、运行时依赖在 `dependencies`）、`extensions/`、`skills/`、`prompts/`、`themes/`。
- 本地验证用 `pi install ./<path>`（按路径加载、不复制）或 `pi -e ./<file>.ts` 单次试用；发布后消费者用 `pi install npm:<name>@<version>` 或 `git:<host>/<repo>@<tag>`，版本化 npm 规格与 git tag 均被锁定；settings 可按 `extensions` / `skills` / `prompts` 过滤加载。
- 供应链：安装使用 `--ignore-scripts`；直接依赖锁精确版本；不依赖其他 pi 包的共享模块实例。
- 独立包的版本与 tag 由 `t-release` 按 [pi 项目协议](${CLAUDE_PLUGIN_ROOT}/protocols/pi-project-contract.md) 产生并同步已有 npm 锁文件（semver 不带 `v`，git tag 带 `v`）；`npm publish` 与消费者侧 `pi install` / `pi update` 由用户手动执行。

修改代码时遵循 [注释契约](${CLAUDE_PLUGIN_ROOT}/protocols/code-comment-contract.md)；完成前按 [validation.md](${CLAUDE_PLUGIN_ROOT}/guides/pi/validation.md) 验证。

库级事实变更时按受影响边界核对官方依据（2026-11-02 核对；具体 API 以项目锁定的 pi 版本为准）：

- 扩展 API、事件顺序、工具定义与截断：[Extensions](https://pi.dev/docs/latest/extensions)，源码 `packages/coding-agent/docs/extensions.md`，参考实现 `packages/coding-agent/examples/extensions/`。
- Skills 发现与 frontmatter：[Skills](https://pi.dev/docs/latest/skills) 与 [Agent Skills 规范](https://agentskills.io/specification)。
- 包清单、安装、依赖与过滤：[Pi packages](https://pi.dev/docs/latest/packages)。
- 设置与资源位置：[Settings](https://pi.dev/docs/latest/settings)；prompt template：[Prompt templates](https://pi.dev/docs/latest/prompt-templates)。
- 沙箱模式：[Containerization](https://pi.dev/docs/latest/containerization)。
