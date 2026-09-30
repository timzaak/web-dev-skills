---
name: t-super-run
description: Plan, execute, repair, and independently accept one explicitly requested delivery phase through a planner and serial role subagents, with persisted item progress and interruption recovery. Use after technical design when planning and execution should run together; use t-task and t-run when the plan needs separate review or execution.
argument-hint: "[任务名称] --phase <backend|frontend|extension|miniapp|web-demo|extension-demo|flutter|flutter-demo>"
allowed-tools:
  - Agent
  - AskUserQuestion
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash
---

# Super Run

一次调用规划、执行并验收 `--phase` 指定的一个阶段。主会话负责门禁、派发、状态、修复路由和遗漏检查；规划交给 `super-run-planner`，实现、测试、验收串行交给对应角色。主会话不写生产代码或测试，不自动执行其他 phase。

## 入口与来源

1. 校验 feature 和必填 `--phase`；支持列表见参数提示。feature 是单个目录名，允许中文、空格、数字、下划线和连字符，拒绝路径分隔符、`.`、`..`。不适用的 phase 终止，不编造交付端。
2. 读取 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`、`${CLAUDE_PLUGIN_ROOT}/protocols/super-run-state-contract.md`。状态、计划产物、恢复和执行规则以该状态协议为准；`.ai/task/` 与本流程独立。
3. 首次规划或来源变化时运行 `python "${CLAUDE_PLUGIN_ROOT}/scripts/check-design.py" ".ai/design/<feature>.md" --require-complete --json`。失败时停止并报告具体问题；`t-design-check`、`t-prd-check`、`t-task-check` 均不作为强制前置。
4. 读取 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` 和 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`；查阅已有 Decision Log、设计引用和相关来源，避免重复提问。把到期的 Deferred Questions 纳入门禁。纯技术方案绕过 PRD 的条件仍由来源协议约束。

## 规划与恢复

- 首次规划、请求 phase 尚未规划或需要重规划时，按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 派发 `${CLAUDE_PLUGIN_ROOT}/agents/super-run-planner.md`。提供目标 phase、设计校验结果、相关来源入口、现有有效计划和证据、待解决问题、下一 revision 的候选目录；只规划请求 phase。
- planner 的输入、输出和审计规则见状态协议的 Planning Contract。先处理 `needs_user_answer`，再接收计划。用户回答先写 Decision Log 并更新事实所属来源，再重派 planner。
- 主会话检查来源分类、责任边界、共享文件/接口冲突、测试选择和验证承接。运行计划审计与决策闭合扫描；通过后由主会话合并状态提案并提交 checkpoint。planner 不得覆盖有效计划或 `.state.json`。
- 重入时先按状态协议处理 `in_progress`、证据失效和旧版本状态，再选择待执行项。相关来源未变且证据有效的 completed item 不重复执行；设计缺失、生成态非 complete 或指纹变化时不得继续派发。

## 串行派发循环

1. 按 manifest 顺序选出首个未完成 item；前序 `in_progress` 或 `blocked` 不能被越过。写入本次 attempt 和 `in_progress`，checkpoint 成功后才派发。
2. 按 subagent-dispatch 注入角色规范，并提供当前 item 全文、阶段 index、必要上游 Handoff、来源与证据入口，以及状态协议的 Dispatch Contract。一次只允许一个 worker 执行；包括内置 runner 在内的 worker 均不得继续派发。
3. worker 先将验证证据写入 item Handoff 或已有运行报告，再返回 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md` 的结构化结果。主会话核对 revision/attempt、实际交付与证据，按状态协议决定完成、补上下文、修复或阻塞。
4. 生产缺陷由主会话派发对应 dev 修复；测试角色保持测试边界。修复、复测、accept 拒绝后的重开均按状态协议执行；accept 独立报告，主会话不得代出或降级其结论。
5. 每次结果、重开或阻塞均提交 checkpoint，重新聚合 slot/phase。仍有可执行 item 时继续，不在 item 之间例行询问是否继续。

只加载当前执行所需内容；主会话可以读取当前 Validation、Handoff 和冲突相关正文，不批量加载全部 item 或后续角色 guide。运行与验收读取 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`，不能以文件存在或 worker 自报成功替代验证。

## 完成与停止

- 只有请求 phase 全部 item 完成或有不适用依据、必要验证有效、accept 通过且最终 checkpoint 成功，才能报告阶段完成。当前 phase 完成后停止，列出其他 phase 和待承接业务验证。
- 最后承接阶段按证据协议核对所有必要场景；不能把“本阶段通过”当成整个 feature 已验收。
- 用户决策、权限或外部条件缺失、无进展重试达到上限、状态无法持久化时保留可恢复现场并停止；不弱化断言、删掉必要 item 或用裁决跳过验收。
- 中断后由同一命令恢复。收尾提供当前 phase/item、改动摘要、证据入口、未完成项和恢复命令。
