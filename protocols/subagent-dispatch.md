# Sub-Agent Dispatch Contract

本协议定义所有 skill 调用子 agent（`Agent` tool）时的角色规范注入规则。它是"子 agent 输入侧"的唯一事实源；输出侧见 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md`。

## 核心规则

通过 `Agent` tool 启动任意子 agent 前，**必须**先 Read `subagent_type` 指向的角色规范文件全文，并把它作为子 agent prompt 的角色指令段注入。

## 注入步骤（MANDATORY）

确定 `subagent_type` 后、调用 `Agent` 工具前：

1. **Read** `${CLAUDE_PLUGIN_ROOT}/agents/` 目录中与 `subagent_type` 同名的 `.md` 文件，取角色规范全文。
   - 文件缺失 → 终止本次调用，提示 `agent "{subagent_type}" 未注册（找不到对应 agent 规范文件）`，不启动子 agent。
2. **注入**：把该全文作为子 agent prompt 的角色指令段（prompt 首段，用清晰分隔标注，例如 `# Agent Role: <name>`），后接本次任务的最小上下文。
3. **调用** `Agent` 工具，`subagent_type` 取原值。

禁止只把 `agents/<name>.md` 路径作为引用放进 prompt、让子 agent 自行按需读取——非 Claude 运行时下子 agent 读不到该文件。

## 同批次同角色复用（token 优化）

注入步骤要求"每次 dispatch 都注入规范"，但**不要求每次都重新 Read 规范文件**。同一次 skill 执行内，若连续多次 dispatch 同一个 `subagent_type`（如多轮修复反复调用 `web-demo-dev`），主会话可在该角色**首次** dispatch 前 Read 一次规范全文，在同批次内复用该注入文本，后续 dispatch 直接复用即可。

边界：

- 角色一旦切换（如 `web-demo-dev` → `backend-dev`），必须重新 Read 新角色规范，不得跨角色复用。
- 新的 skill 调用、批次重入或会话切换后，不复用上一批次的缓存注入文本，重新 Read。
- 注入文本本身仍是每次 dispatch 必须出现在子 prompt 首段；复用的是"主会话读取"这一步，不是"注入"这一步。

动机：每个 agent 规范文件常达百行以上，在多失败用例、同一修复 agent 反复上场的批次里，每次 dispatch 都重新 Read 会让主会话上下文被规范全文反复占位。读一次、注入多次，能把这部分开销降到固定成本。

## 适用范围

适用于所有调用 `Agent` tool 的 skill，包括但不限于：`t-run`、`t-task`、`t-task-check`、`t-web-demo-run`、`t-flutter-demo-run`、`t-init`、`t-dream`、`t-html-show`、`t-prd`、`t-decision`、`t-doc`、`t-simplify`。

`general-purpose` / `general_agent` 等内置通用 agent 无 `agents/*.md` 定义，跳过注入步骤。

## 边界事实

`agents/*.md` 不被非 Claude 运行时自动加载这一边界，见 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md` 的 Runtime Rules。
