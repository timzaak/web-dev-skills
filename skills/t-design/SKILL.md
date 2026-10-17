---
name: t-design
description: Generate an actionable technical design from confirmed requirements and actual project modules; use after PRD or purely technical research, before implementation planning.
argument-hint: "<feature>"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - Agent
---

# 技术设计

将真实需求与项目约束收敛为 `.ai/design/<feature>.md`、必要的模块设计和 `.ai/design/<feature>/.state.json`，不预设语言、框架或交付端。

## 输入与门禁

- feature 为单个目录名，拒绝路径分隔符、`.`、`..`；参数缺失时提示 `/t-design <feature>`。
- 先读 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md` 与 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`，从索引定位相关 `.ai/prd/`、`docs/prd/`、draft/published 用户故事和技术预研。按 feature 搜索草稿，不能因索引未收录而遗漏；草稿与基线并存必须核对差异及授权关系。
- 读取 `.ai/decision/<feature>.md`、`.ai/decision-log/<feature>.md`（存在时）；提问与决策闭合遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`，复用已确认决定，不采用 Superseded Decision。
- 只有不改变业务逻辑、产品规则、用户流程或验收目标的纯技术方案，才可仅依赖 `.ai/tech-research/<feature>.md`；明确记录不涉及业务变动的边界。
- 影响范围、公共契约、权限、兼容、测试策略或形成项目新约束的工程偏好的缺口未解决时，通过 AskUserQuestion 暴露，回答前不得写成假设后继续。`t-prd-check` 是可选检查。

## 流程

1. 读取目标项目 AGENTS.md、相关代码、配置、项目规范与已有验证入口；只分析当前范围。项目事实或需求冲突先解决，不套用插件技术栈。
2. 按真实责任边界确定模块 ID 与设计路径，在主文档 §4.2 声明；小项目可用 `main` 路径在主文档内设计。跨模块契约在 §4.3 指明唯一来源；生产者先设计，消费者只引用，不复制定义。需要新模块或新目录时给出命名依据。
3. 写状态前读取 `${CLAUDE_PLUGIN_ROOT}/protocols/design-state-contract.md`；首次写 in_progress。已有文件先检查用户授权，保留用户修改；恢复时重读来源，只重做失效模块，不能覆盖原状态后当新任务执行。
4. 对独立模块读取 `${CLAUDE_PLUGIN_ROOT}/agents/project-design.md`，按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 注入角色并调度，传入需求/决策、模块相关事实、契约源、输出路径和 `${CLAUDE_PLUGIN_ROOT}/protocols/design-agent-output-contract.md`。小项目主会话按同一角色约束完成主文档。partial/failed 或 needs_user_answer 未清空时不进入合并，无法恢复时写 failed。
5. 使用 `${CLAUDE_PLUGIN_ROOT}/skills/t-design/template.md` 合并主文档，覆盖完整 Decision Trace、需求覆盖矩阵、模块导航、契约摘要、测试与文件影响。模块文件必须有 `## 8. 文件影响范围`，主文档逐行汇总。测试责任按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`，命令来自项目实际入口。
6. 对全部实际设计文件运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py <实际文档路径列表>`，处理命中项；再运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/check-design.py .ai/design/<feature>.md`。全部通过且适用模块均成功，才写 complete。高风险设计额外用无原会话背景的只读角色检查实现入口、契约源、失败路径与测试证据。

## 输出与恢复

报告文档与状态路径、适用模块、已复用或新增的 DEC/Q、验证结果、剩余风险。推荐复杂设计先做可选 `/t-design-check <feature>`；否则进入 `/t-super-run <feature> --phase <phase>`，phase 从 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 获取。

状态损坏、来源不足、路径不存在或写入失败时停止并报告具体原因；保留中间产物，同一命令恢复。结构校验只证明可消费结构，不能替代实现后的 accept。
