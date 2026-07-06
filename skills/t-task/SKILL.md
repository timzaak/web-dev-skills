---
name: t-task
description: Convert technical design documents into executable phased task plans with work breakdown and dependencies.
argument-hint: "[任务名称] [--phase <backend|frontend|miniapp|demo>]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Task
  - Write
  - Bash
  - Agent
---

# 任务规划生成

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
需求来源边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`

任务拆分必须服务于边界清楚、失败可定位、验证闭环明确的执行；如果设计文档、guide 或 protocol 冲突，停止并说明冲突。

影响规划方向的缺口必须通过 `AskUserQuestion` 解决，不得把问题写成 P0/P1、假设或 handoff 后继续生成任务。

## Input Contract

上游输入（来自 `/t-design` 产出）：
- `.ai/design/[feature].md` — 技术设计文档（必须存在）
  - 必须包含：目标、范围、API 接口设计、数据库设计、测试策略
  - 应包含：现有实现分析、用户故事/PRD/技术预研引用、文件影响范围
  - 纯技术方案设计可只包含技术预研引用，但必须声明不涉及业务逻辑、产品规则、用户可见流程或验收目标变动

可选输入：
- `.ai/task/[feature]/.state.json` — 已有任务状态（增量生成时）
- `docs/prd/**/*.md` — PRD 文档
- `.ai/user-stories/**/*.md` — draft 用户故事
- `docs/user-stories/**/*.md` — 已发布用户故事
- `.ai/tech-research/**/*.md` — 技术预研报告
- `${CLAUDE_PLUGIN_ROOT}/guides/` — 开发规范

## Output Contract

下游产出：
- `.ai/task/[feature]/.state.json` — 任务状态文件，包含 phase/slot/item 层级状态
- `.ai/task/[feature]/<phase>/index.md` — 阶段总览
- `.ai/task/[feature]/<phase>/<slot>.md` — Slot manifest（导航与依赖）
- `.ai/task/[feature]/<phase>/<slot>/<ITEM-ID>-*.md` — 可执行的 item 文件

状态结构、item 字段、slot 顺序、测试集中执行和 backend/test 特殊字段统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md`

## Purpose
- 从 `.ai/design/[feature].md` 生成 `.ai/task/[feature]/` 任务目录和 `.state.json`。
- 固定使用 `phase -> slot -> item` 模型。
- 生成串行执行的 item 文件，而不是把 manifest 当执行输入。

## Args
| 参数 | 说明 |
|---|---|
| `[feature]` | 功能名（必填） |
| `--phase <backend\|frontend\|miniapp\|demo>` | 指定阶段生成；未指定时自动选择第一未完成阶段 |

## Preconditions
- `.ai/design/[feature].md` 必须存在。
- 阶段依赖、active phases、miniapp 启用规则和 slot 顺序统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md`

## Output Layout
按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的 active phases 和 slot order 生成：

- `.ai/task/[feature]/<phase>/index.md`
- `.ai/task/[feature]/<phase>/<slot>.md`
- `.ai/task/[feature]/<phase>/<slot>/<ITEM-ID>-*.md`

## Generation Flow
- 校验 `.ai/design/[feature].md` 存在。
- 解析 `[feature]` 和 `--phase`；根据 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 检测 active phases；未传 `--phase` 时自动选择第一未完成 active phase。
- 按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 校验阶段前置和 slot 顺序；未启用的 phase 不参与校验或生成。
- 若设计文档存在会影响任务拆分、交付范围、权限/安全边界、数据模型、兼容性策略、验收标准或测试闭环的未决问题，先使用 `AskUserQuestion` 获取用户答案；回答前不得生成或更新 `.ai/task/[feature]/`。
- 按当前 phase 提取设计文档最小相关上下文；未命中相关章节时记录警告，但不得编造设计事实。
- 调度 slot agent 前，先要求其识别当前 slot 的责任闭环：业务能力、接口能力、页面主流程、组件族、测试资产闭环或验收闭环；技术层、文件类型和实现步骤只作为拆分的辅助线索。
- 按当前阶段 slot 串行调度相应 agent。每个 slot agent 必须按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 通过 `Agent` tool 启动，`subagent_type` 按 Agent Dispatch Mapping 映射。
- 传入 agent prompt 的内容保持精简：阶段设计摘要、上游 handoff、目标 guide/protocol 路径、责任闭环识别要求、输出字段要求、`needs_user_answer` 规则；不得复制 guide、protocol 或 agent 文档中的长篇规则。
- slot agent 返回结构统一参考 [Agent Output Contract](#agent-output-contract)。
- 主流程在每个 slot 返回后先执行写入前硬校验：
   - item 必填字段齐备
   - item ID 唯一，依赖存在且无环
   - manifest 覆盖全部 items，路径与 item 文件一致
   - 符合 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 和 `${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md` 的 P0/P1 硬门禁
- 硬校验失败时终止当前 slot，不写入成功状态，要求重新生成该 slot。
- 硬校验通过后写入当前 slot manifest 和 item 文件，再继续调用下游 slot。
- 当前阶段 slot 齐备后生成 `<phase>/index.md`。
- 写入或更新 `.state.json`。
- 返回下一步建议：`/t-task-check [feature] --phase [phase]`。

## Agent Dispatch Mapping

| phase | slot | subagent_type |
|-------|------|---------------|
| backend | dev | backend-dev |
| backend | test | backend-test |
| backend | accept | backend-accept |
| frontend | dev | frontend-dev |
| frontend | test | frontend-test |
| frontend | accept | frontend-accept |
| miniapp | dev | miniapp-dev |
| miniapp | test | miniapp-test |
| miniapp | accept | miniapp-accept |
| demo | dev | demo-dev |
| demo | accept | demo-accept |

## Slot Manifest Contract
每个 slot manifest 必须包含：
- slot 目标和边界
- item 表格：`id | title | agent | file | depends_on`
- 必要的上游输入和下游 handoff 摘要

manifest 不得包含完整实现步骤；完整步骤必须写入 item 文件。

## Generated Document Style

任务文档面向 `/t-run` 执行与恢复，不承载教程或指南复述：

- 只写当前 feature、phase、slot、item 的可执行事实。
- 引用 guide、protocol、agent 文档路径，不复制其中的长篇规则。
- item 正文只使用 `Goal / Work / Files / Validation / Handoff` 五个章节。
- `Work` 写具体动作，不写通用工程原则。
- `Validation` 写目标项目真实命令、脚本或验收证据，不写抽象测试建议。
- item 应写明失败边界：失败时定位到哪类问题、由哪个 agent/slot 继续处理。
- `Handoff` 只保留给下游 slot/agent 必需的信息；没有下游依赖时写 `None`。

## Agent Output Contract
slot agent 输出必须至少包含：
- `slot`: `dev|test|accept`
- `manifest_target_file`
- `manifest_content`
- `items`: item 对象列表，每个 item 包含 `id/file/agent/depends_on/content`
- `item_dag`
- `self_check`: 必填字段、DAG、责任闭环拆分、过度拆分、阶段执行规则和 P0/P1 风险自检结果

主流程必须：
- 校验 `slot` 与被调度 agent 是否匹配。
- 校验 item 依赖合法且无环。
- 校验 manifest、item 文件路径和 `.state.json` 计划一致。
- 校验 item 使用 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的最小结构。
- 校验 `self_check` 存在且未声明未解决 P0/P1。
- 校验 slot agent 已说明 item 的责任闭环；若存在把技术层、文件类型或实现步骤当成唯一拆分依据、重复验证命令或不可独立验收的过度拆分，拒绝写入成功状态。
- 先写入当前 slot manifest 和 item 文件，再继续调用下游 slot。
- 在当前阶段要求的 slot 结果齐备后再生成 `index.md`。
- 文档写入与 `.state.json` 更新保持同轮完成。

## Item Contract And Splitting

item 字段、backend/test item 类型、测试集中执行规则、拆分原则、Cargo package 名核验要求统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md`

本 skill 只负责把 agent 返回结果校验并写入 `.ai/task/[feature]/`，不在这里维护第二套 item 结构或拆分阈值。

## Forbidden
- 生成或依赖 `agents` 根字段。
- 把 `dev.md`、`test.md`、`accept.md` 当作 `/t-run` 的直接执行输入。
- 当前阶段 slot 并行生成；slot 必须按依赖串行。
- 未写入上游 manifest 和 item 文件就调用下游 slot agent。
- 在任务文档中复制 guide/protocol/subagent 的长篇指南。
- 在 item 中写与当前交付无关的通用实现建议、培训内容或风格偏好。
- 违反 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的拆分、测试集中执行或 backend/test runner 规则。

## Failure
- 设计文档不存在：提示先运行 `/t-design [feature]`。
- 前置阶段未完成：返回阻塞阶段、当前状态、阻塞 items/slots 和下一步命令；不得修改 `.state.json`。
- 任一 slot agent 生成失败：终止本次任务生成，不写入该 slot 的成功状态，并返回失败 agent 与失败原因。
- slot agent 返回 item 缺少必填字段、依赖不存在或形成环：拒绝写入成功状态，要求重新生成该 slot。
- slot agent 返回缺失 `self_check`、manifest 覆盖不完整、backend/test 类型非法、触发必须拆分规则或明显过度拆分：拒绝写入成功状态，要求重新生成该 slot。
- slot agent 返回 `needs_user_answer`：使用 `AskUserQuestion` 向用户提问，回答前不写入该 slot；回答后先同步设计/规划依据，再重新生成该 slot。

## Examples
```bash
# 生成 backend 阶段任务
/t-task <feature> --phase backend

# 未指定 phase 时自动选择第一未完成阶段
/t-task <feature>
```

期望响应：
```text
已生成 backend 阶段任务：
- index.md
- dev.md + dev/*.md
- test.md + test/*.md
- accept.md + accept/*.md

状态已更新：phase=backend, phases.backend.status=generated
下一步: /t-task-check <feature> --phase backend
```
