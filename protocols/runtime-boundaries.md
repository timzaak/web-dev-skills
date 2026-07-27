# Runtime Boundaries

本协议定义目标项目运行时事实与插件资源的边界。skill 和 agent 在读取上下文、写入产物及选择脚本入口时必须遵循本协议。

## Ownership

| 位置 | 职责 |
| --- | --- |
| 目标项目代码与配置 | 当前实现事实 |
| 目标项目 `AGENTS.md` / `CLAUDE.md` | 项目级执行约束 |
| 目标项目 `docs/` | 已发布的长期产品、设计和使用事实 |
| 目标项目 `.ai/` | 当前工作流的草稿、状态、质量报告和预览产物 |
| 目标项目 `scripts/` | 环境、测试和 Demo 的本地执行入口 |
| `${CLAUDE_PLUGIN_ROOT}/protocols/` | 跨 skill 和 agent 的共享契约 |
| `${CLAUDE_PLUGIN_ROOT}/guides/` | 默认工程规范和领域实践 |
| `${CLAUDE_PLUGIN_ROOT}/skills/` | 阶段入口和编排逻辑 |
| `${CLAUDE_PLUGIN_ROOT}/agents/` | subagent 角色边界和执行职责 |

插件资源不是目标项目的业务事实来源。目标项目可以在不破坏共享契约的前提下覆盖插件默认规范。

## Resolution Rules

- 当前实现行为以目标项目代码和配置为准。
- 项目执行约束以目标项目 `AGENTS.md` / `CLAUDE.md` 为准。
- 长期项目事实从目标项目代码、配置和 `docs/` 读取；`.ai/` 中的内容视为当前流程产物，只有通过相应发布阶段写入 `docs/` 后才成为长期文档。
- 跨阶段的结构化字段、状态、报告格式、评分规则和命令契约以 `${CLAUDE_PLUGIN_ROOT}/protocols/` 为准。
- 项目没有更具体约束时，采用 `${CLAUDE_PLUGIN_ROOT}/guides/` 中的默认规范。
- 不同来源冲突时不得静默覆盖；应报告冲突、涉及的来源以及继续执行需要采用的规则。

PRD、用户故事和技术预研的正式来源与候选来源边界见 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`。跨阶段已确认决策、已解决问题和延期问题写入目标项目 `.ai/decision-log/`，结构与门禁见 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`。

## Script Entry Rules

运行环境、测试和 Demo 脚本时：

1. 目标项目存在 `scripts/<name>.py` 时，使用 `uv run scripts/<name>.py ...`。
2. 目标项目缺少该脚本时，才回退到 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py ...`。
3. 目标项目脚本存在但执行失败时，不得用插件脚本绕过；应报告失败原因。

项目可以调整本地脚本内部的 Docker 镜像、容器名、端口、环境变量和启动命令，但脚本文件名、主要命令行参数、JSON 输出和日志契约必须保持稳定。

## Subagent Runtime

`${CLAUDE_PLUGIN_ROOT}/agents/*.md` 在非 Claude 运行时不保证自动加载。skill 调用子 agent 前，必须按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 显式注入角色规范。
