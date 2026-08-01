---
name: t-super-run
description: Plan and execute a backend, frontend, or demo phase in one persistent main-session Goal with outcome-level status, role-guide switching, validation, recovery, and acceptance loops, without dispatching subagents.
argument-hint: "[任务名称] [--phase <backend|frontend|demo>]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash
  - WebSearch
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
---

# Super Run

把任务规划与阶段执行合并为一个可恢复闭环。只做 `phase -> task` 目标级规划，由当前主会话直接完成实现、测试、修复和验收，不调用 subagent。

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

需求与决策边界统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`

计划、状态、角色映射、执行顺序、恢复、验收回退和 Goal 规则统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/super-run-state-contract.md`

## Args

| 参数 | 说明 |
| --- | --- |
| `[feature]` | 必填；允许中文、英文、数字、空格、下划线和连字符 |
| `--phase <backend\|frontend\|demo>` | 可选；未传时选择首个适用且未完成的 phase |

## Preconditions

- `.ai/design/[feature].md` 必须存在。
- 只支持 `backend | frontend | demo`。miniapp 和 Flutter 使用 `/t-task`、可选 `/t-task-check` 与 `/t-run`。
- 不读取或修改 `.ai/task/[feature]/` 作为 super-run 状态。

## Source Loading

在规划或恢复前：

1. 读取目标项目 `.ai/design/[feature].md` 和现有 `.ai/super-run/[feature]/`。
2. 读取相关 `.ai/prd/**/*.md`、`docs/prd/**/*.md`、`.ai/user-stories/**/*.md` 与 `docs/user-stories/**/*.md`，保留 draft/published 来源边界。
3. 在任何提问前读取 `.ai/decision-log/[feature].md`；存在时按需读取 `.ai/decision/[feature].md` 与 `.ai/tech-research/[feature].md`。
4. 检查设计引用、Decision Trace、目标项目代码和配置，确定 active phases、真实验证入口和当前实现事实。
5. 把事实缺口、工程决策、用户决策和验证动作按 Decision Exposure Gate 分类；`needs_user_answer` 未解决时不得进入实现。

不要无差别加载所有 PRD、用户故事或 guide。先通过 feature 名、设计引用和内容检索定位相关文件，再读取全文。

## Plan And State

- 按 `${CLAUDE_PLUGIN_ROOT}/protocols/super-run-state-contract.md` 创建或更新：
  - `.ai/super-run/[feature]/.state.json`
  - `.ai/super-run/[feature]/[phase].md`
- backend/frontend 固定规划 `dev -> test -> accept`，demo 固定规划 `dev -> accept`。
- 每个 task 只规划一个责任闭环，不生成 item。
- 计划必须写明每个 task 要读取的 agent 规范及其关联文档的具体路径。
- demo/dev 的关联文档必须包含 `${CLAUDE_PLUGIN_ROOT}/agents/demo-diagnose.md`，用于把 Demo 失败归因到测试资产、frontend 或 backend 后再切换对应规范修复。
- 首次写入后或恢复到未完成 phase 后，主动调用 `/goal` 或运行时等价 Goal API；Goal 的 outcome、constraints 和 verification 必须符合共享协议。

规划写清目标、成功标准、权限边界、当前角色、证据入口和停止条件，具体实现路径根据仓库事实决定。不要把 `t-task` 的细粒度 item 换一种格式复制进来，也不要用长篇过程指令占用持续 Goal 的上下文。

## Execute

循环执行直到 phase 完成或进入真正阻塞：

1. 按状态选择顺序中的第一个 `pending | in_progress | failed` task。
2. 读取该 task 的 agent 规范全文及计划列出的关联文档，把它们作为主会话当前角色边界。
3. 写入 `in_progress`，执行交付、最小可靠验证和必要修复。
4. 写入 `completed` 与证据，重新聚合 phase，继续下一个 task。
5. 失败时先写 `failed` 与证据；能够基于新证据修复时继续闭环，否则写 `blocked` 并暂停 Goal。
6. accept 拒绝时按共享协议重新打开 dev 或 test，再次测试和验收。

每次显著步骤后把完成内容、验证证据、剩余工作和 handoff 写入状态或 phase 计划，确保上下文压缩后能从文件恢复。

## Forbidden

- 调用 `Agent`、并行 subagent 或任何以 subagent 做上下文隔离的调度。
- 生成 `.ai/task/` 的 manifest/item，或修改 `t-task/t-run` 状态。
- 把 accept 角色改为实现角色，或让 accept 直接修复代码。
- 跳过测试、弱化断言、忽略失败或把 `blocked` 当作 Goal 完成。
- 在无真实兼容约束时保留被设计明确替换的旧路径。

## Completion

只有同时满足以下条件才完成 Goal：

- 当前 phase 的全部 task 为 `completed | skipped`。
- 计划中的验证已经执行并有证据。
- accept task 给出允许进入下游的结论；整个 phase 为 `skipped` 时必须有明确不适用证据。
- `.state.json` 已按最终结果聚合。

输出当前 phase、task 状态、主要变更、验证证据和下一未完成 phase。若全部 active phases 已完成，明确报告 feature 的 super-run 已完成。
