# Runtime Boundaries

本协议定义目标项目运行时事实与插件资源的边界。skill 和 agent 在读取上下文、写入产物及选择脚本入口时必须遵循本协议。

## Ownership

| 位置 | 职责 |
| --- | --- |
| 目标项目代码与配置 | 当前实现事实 |
| 目标项目 `AGENTS.md` | 项目级执行约束 |
| 目标项目 `docs/` | 已发布的长期产品、设计和使用事实 |
| 目标项目 `.ai/` | 当前工作流的草稿、状态、质量报告、预览产物，以及 Figma 工作目录和原始证据 |
| 目标项目 `scripts/` | 环境、测试和 Demo 的本地执行入口 |
| 目标项目 skill 目录（`.claude/skills/`、`.agents/skills/` 等按项目运行时） | 项目级 AI 能力资产，由 `t-skill --project` 和 skill 交付 task 写入 |
| `${CLAUDE_PLUGIN_ROOT}/protocols/` | 跨 skill 和 agent 的共享契约 |
| `${CLAUDE_PLUGIN_ROOT}/guides/` | 通用工程指南，以及保留的 Web Demo / Figma 实践 |
| `${CLAUDE_PLUGIN_ROOT}/skills/` | 阶段入口和编排逻辑 |
| `${CLAUDE_PLUGIN_ROOT}/agents/` | subagent 角色边界和执行职责 |
| `${CLAUDE_PLUGIN_ROOT}/templates/project-profiles/` | 显式选择后导出的领域源模板，不自动加载到当前运行时 |

插件资源不是目标项目的业务事实来源。目标项目可以在不破坏共享契约的前提下覆盖插件默认规范。

## Resolution Rules

- 当前实现行为以目标项目代码和配置为准。
- 项目执行约束以目标项目 `AGENTS.md` 为准。
- 长期项目事实从目标项目代码、配置和 `docs/` 读取；`.ai/` 中的内容视为当前流程产物，只有通过相应发布阶段写入 `docs/` 后才成为长期文档。
- 跨阶段的结构化字段、状态、报告格式、评分规则和命令契约以 `${CLAUDE_PLUGIN_ROOT}/protocols/` 为准。
- 项目工程规则来自目标项目已确认文档；插件仅提供通用流程、Web Demo 与 Figma 指南，不推断默认技术栈。
- 不同来源冲突时不得静默覆盖；应报告冲突、涉及的来源以及继续执行需要采用的规则。

PRD、用户故事和技术预研的正式来源与候选来源边界见 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`。跨阶段已确认决策、已解决问题和延期问题写入目标项目 `.ai/decision-log/`，结构与门禁见 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`。

## Optional Template Runtime

需要现成领域资产时，读取 `${CLAUDE_PLUGIN_ROOT}/templates/index.md` 并显式选择模板。export-template.py 只导出到本仓库外的独立插件目录；files/ 的资源必须与 template.json 指定来源提交的共享运行时配套使用，不能覆盖当前插件的 phase/state/output 契约。导出的 .t-tools-template.json 记录来源供维护，不是目标项目工作流状态。同一运行会话只加载通用插件或一份导出模板。

模板原文中的 `${CLAUDE_PLUGIN_ROOT}` 在导出后指向独立插件根；通用链接检查不把未实例化的 files/ 当成当前插件文件，导出后须用 check-markdown-links.py --root 验证实际引用。维护模板来源或持续合并 main 时读取仓库 human/merge-main.md。

## Script Entry Rules

运行插件提供的测试和 Demo 工具时：

1. 目标项目存在 `scripts/<name>.py` 时，使用 `uv run scripts/<name>.py ...`。
2. 目标项目缺少该脚本时，才回退到 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py ...`。
3. 目标项目脚本存在但执行失败时，不得用插件脚本绕过；应报告失败原因。

项目自有验证命令内部由项目维护。保留工具的主要 CLI、JSON 输出与日志契约保持稳定。应用环境 hook（scripts/demo-start.py、demo-health.py、demo-stop.py）与项目 CI（scripts/ci.py）只允许调用目标项目本地入口，不回退插件；环境由 fixture/外部管理时 runner 使用 --no-auto-env。

## Subagent Runtime

`t-super-run` 的目标级阶段计划、状态与证据入口位于目标项目 `.ai/super-run/<feature>/`，布局及主会话执行边界见 `${CLAUDE_PLUGIN_ROOT}/protocols/super-run-state-contract.md`。由该入口按需创建，不由 `t-init` 预生成，也不复用 `.ai/task/` 状态。

`${CLAUDE_PLUGIN_ROOT}/agents/*.md` 在非 Claude 运行时不保证自动加载。skill 调用子 agent 前，必须按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 显式注入角色规范。
