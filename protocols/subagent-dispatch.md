# Sub-Agent Dispatch Contract

## Dispatch

调用 `Agent` 前：

1. 确定 `subagent_type`。
2. Read `${CLAUDE_PLUGIN_ROOT}/agents/` 下与 `subagent_type` 同名的 `.md` 文件全文。
3. 把全文放在 prompt 首段，标记为 `# Agent Role: <subagent_type>`。
4. 追加本次任务的最小上下文，再调用 `Agent`。

角色文件缺失时停止，返回：`agent "<subagent_type>" 未注册`。不得只把角色文件路径交给子 agent；非 Claude 运行时不保证可读取插件文件。

`general-purpose`、`general_agent` 等没有角色文件的内置通用 agent 跳过注入。

## Reuse

同一次 skill 执行内，同一角色可只 Read 一次，但每次 dispatch 仍要注入全文。角色切换、skill 重入或会话切换后重新 Read。

## Output

- 实现、修复、测试、验收 agent：`${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md`
- backend/frontend/flutter design agent：`${CLAUDE_PLUGIN_ROOT}/protocols/design-agent-output-contract.md`
