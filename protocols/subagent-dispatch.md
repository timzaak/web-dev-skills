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

## 适用范围

适用于所有调用 `Agent` tool 的 skill，包括但不限于：`t-run`、`t-task`、`t-task-check`、`t-demo-run`、`t-init`、`t-dream`、`t-html-show`、`t-prd`、`t-decision`、`t-doc`。

`general-purpose` / `general_agent` 等内置通用 agent 无 `agents/*.md` 定义，跳过注入步骤。

## 边界事实

`agents/*.md` 不被非 Claude 运行时自动加载这一边界，见 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md` 的 Runtime Rules。
