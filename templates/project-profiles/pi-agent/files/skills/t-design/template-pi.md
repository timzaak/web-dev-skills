# [方案名称] pi 扩展技术设计

主文档：`.ai/design/[feature].md`。仅描述 pi 交付（extension、随包 skill、package 清单）；后端契约引用来源，不复制字段定义。

## 1. 目标与范围

- [本端交付目标、范围外项、项目锁定的 pi 版本、包形态（独立 pi package / 项目级 `.pi/` 资源 / 首次交付）与运行模式（tui / rpc / json / print）；使用有版本门槛的扩展 API 时说明兼容策略；适用性按 `${CLAUDE_PLUGIN_ROOT}/protocols/pi-project-contract.md`]

## 2. 需求来源与决策追踪

| Decision ID | 状态 | 设计落点 | 说明 |
|---|---|---|---|
| `DEC-[feature]-001` | Applied / Not Applicable / Superseded | [章节] | [依据] |

- [需求/用户故事/纯技术预研引用及验收目标]

## 3. 现有实现分析

- [真实 `package.json` 清单与 scripts、现有扩展入口、已注册工具/命令/事件、resources 目录、settings 过滤、可复用模块与受影响边界]

## 4. 扩展入口与工具契约

- 扩展入口：[文件路径、工厂同步/异步、注册时机（加载期 / `session_start`）、后台资源启动与 `session_shutdown` 清理]

| 工具名 | 参数 schema（typebox） | exposure | 输出截断 | 并发模式 | 用途与 `promptGuidelines` |
|---|---|---|---|---|---|
| [tool_name] | [字段、枚举、必填] | direct / model-only / codemode / deferred | [truncateHead / truncateTail 与上限；无界输出的完整结果落点] | parallel / sequential；[改文件时 withFileMutationQueue 范围] | [点名工具的 guideline] |

- 错误与终止：[抛错或 `isError` 的选择、`terminate` 条件、嵌套模型调用的 `usage` 上报]
- 覆盖内置工具（适用时）：[被覆盖工具、保持的结果形状与 `details` 类型、渲染槽继承]

## 5. 命令、事件钩子与阻塞语义

| 命令 / 事件 | 触发 | 行为 | 阻断 / 转换 / 通知 | 守卫条件 |
|---|---|---|---|---|
| [/command 或 event_name] | [用户 / 模型 / 生命周期] | [主路径] | [返回值语义] | [continue / block 的前置条件；安全门 fail closed] |

- 系统提示修改：[走 `systemPromptOptions.sections` / `selectedTools` / `promptGuidelines`，或整体替换的设计依据]
- `context` / `context_with_system`（适用时）：[修改范围与索引 0 system message 保留]

## 6. 状态与持久化

- 工具状态：[存入 `details` 的结构；`session_start` / `session_tree` 从 `getBranch()` 重建的函数]
- 非模型数据：[`appendEntry` 的 customType 与渲染；进入模型上下文的 `sendMessage` 消息]
- 跨会话替换：[`/new` `/resume` `/fork` `/reload` 时清理与重建；`withSession` 只用新 ctx]

## 7. UI 与运行模式

- 对话与通知：[`select` / `confirm` / `input` / `notify` / `setStatus` / `setWidget` 的使用点与 `ctx.hasUI` 守卫]
- 自定义组件（适用时）：[`ctx.ui.custom()` 与渲染器；限 `ctx.mode === "tui"`]
- print / json / rpc 下的行为：[无 UI 时的降级路径；不依赖 UI 返回值]

## 8. Provider、MCP、依赖与清单

### 8.1 API 依赖

- 契约源：[backend.md 或现有 OpenAPI/SDK；无后端时明确不适用并删除示例行]

| Operation ID | 方法 | 路径 | 使用的请求字段 | 使用的响应字段 | 用途 |
|---|---|---|---|---|---|
| [operationId] | [METHOD] | `/api/...` | [字段名] | [字段名] | [用途] |

### 8.2 Provider 与 MCP

- Provider（适用时）：[`registerProvider` 名称、api 类型、`apiKey` 来源；模型调用走 `ctx.modelRegistry`]
- MCP（适用时）：[`registerMcpServer` 名称与 config；与 `mcp.json` 同名优先的处理]
- 外部进程：[`pi.exec` 命令、超时与 `ctx.signal` 传递]

### 8.3 依赖与清单

- 运行时依赖：[新增 `dependencies` 及精确版本与依据；host 包只在 `peerDependencies`]
- 清单：[`pi.extensions` / `skills` / `prompts` / `themes` 路径或 glob；`keywords` 与 `changelogPath`]
- 权限与安全：[`tool_call` 门或容器化落点；project trust 相关行为；不引入远程代码加载]

## 9. Skills 交付（适用时）

- [skill 名称、`description` 触发条件、`disable-model-invocation`、references/scripts 清单；写作按 `${CLAUDE_PLUGIN_ROOT}/guides/core/skill-authoring.md`，不适用时写明]

## 10. 测试与验收

- Vitest（按需）：[schema 边界、`prepareArguments`、纯函数、状态重建、权限门判定；可观察回归与覆盖缺口；无增量价值时写“不新增”及原因]
- 运行时冒烟：[`pi -e <file> --mode json -p "<提示>"` 或 TUI `/reload` 后触发；期望的事件流/工具名/结果；所需 provider 与鉴权状态；按 `${CLAUDE_PLUGIN_ROOT}/guides/pi/testing.md` 规划]
- 包形态：[隔离测试配置下 `pi -e ./<path>` 临时加载后的资源发现与过滤验证；需要测试安装时说明隔离方式；不适用时说明]
- 类型检查与 lint：[实际脚本名或已有本地编译器命令；纯资源文本无需类型检查时说明依据；不安装临时工具]

## 11. 风险与验证动作

- [已确定方案的风险、验证动作及完成条件；用户裁决缺口返回主会话，不以假设推进]

## 12. 文件影响范围（pi 文件）

| 文件 | 操作 | 说明 |
|---|---|---|
| `[真实仓库路径]` | CREATE / MODIFY / DELETE | [变更与命名依据] |

同时列入随包分发的 skill、prompt、theme 资源；skill 交付物在主文档汇总时按归属标注。路径校验与新 skill 目录例外按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的 Skill Deliverables 执行。
