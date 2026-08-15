---
name: t-task
description: Convert technical design documents into executable phased task plans with ordered work breakdown.
argument-hint: "[任务名称] [--phase <backend|frontend|miniapp|flutter|web-demo|flutter-demo>]"
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
决策连续性和用户决策暴露统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`

任务拆分必须服务于边界清楚、验证闭环明确的执行；如果设计文档、guide 或 protocol 冲突，停止并说明冲突。

影响规划方向的缺口必须通过 `AskUserQuestion` 解决，不得把问题写成 P0/P1、假设或 handoff 后继续生成任务。

## Input Contract

上游输入（来自 `/t-design` 产出）：
- `.ai/design/[feature].md` — 设计主文档（必须存在）
  - 必须包含：目标、范围、交付端范围、跨端契约摘要、测试与验收汇总、文件影响范围全量汇总
  - 应包含：现有实现分析概览、用户故事/PRD/技术预研引用、Decision Trace
  - 纯技术方案设计可只包含技术预研引用，但必须声明不涉及业务逻辑、产品规则、用户可见流程或验收目标变动
- `.ai/design/[feature]/backend.md`、`.ai/design/[feature]/frontend.md`、`.ai/design/[feature]/flutter.md` — 分端设计文档；主文档 §4.2 标记适用时必须存在，生成对应 phase 时必须读取（API 契约、数据库设计等分端细节以分端文档为准）
- `.ai/decision-log/[feature].md` — 跨阶段决策账本（存在时必须读取；本阶段不得采用 Superseded Decision）

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
- `.ai/task/[feature]/<phase>/index.md` — 阶段总览，包含当前 phase 的 Decision Trace
- `.ai/task/[feature]/<phase>/<slot>.md` — Slot manifest（导航与执行顺序）
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
| `--phase <backend\|frontend\|miniapp\|flutter\|web-demo\|flutter-demo>` | 指定阶段生成；未指定时默认选择第一个 active phase |

## Preconditions
- `.ai/design/[feature].md` 必须存在。
- active phases、miniapp 启用规则和 slot 顺序统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md`

## Output Layout
按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的 active phases 和 slot order 生成：

- `.ai/task/[feature]/<phase>/index.md`
- `.ai/task/[feature]/<phase>/<slot>.md`
- `.ai/task/[feature]/<phase>/<slot>/<ITEM-ID>-*.md`

## Generation Flow
- 校验 `.ai/design/[feature].md` 存在。
- 读取 Decision Log，核对设计的 Decision Trace，并把 `Must Resolve Before=t-task` 的 Deferred Question 升级为 `needs_user_answer`。
- 解析 `[feature]` 和 `--phase`；根据 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 检测 active phases；未传 `--phase` 时选择第一个 active phase。
- 按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 校验当前 phase 是否启用和 slot 顺序；未启用的 phase 不参与生成。
- 若设计文档或 Decision Log 存在会影响任务拆分、交付范围、权限/安全边界、数据模型、兼容性策略、验收标准或测试闭环的未决问题，先按 Topic 检查既有决定；仍未解决时使用 `AskUserQuestion` 获取用户答案。回答后先更新 Decision Log 和设计文档；完成前不得生成或更新 `.ai/task/[feature]/`。
- 按当前 phase 提取设计文档最小相关上下文：主文档（目标范围、交付端范围、跨端契约、测试汇总、文件影响范围）加当前 phase 对应的分端设计文档（backend phase 读 `backend.md`，frontend phase 读 `frontend.md`，flutter/web-demo/flutter-demo phase 读对应端文档，缺失时读主文档可用部分）；未命中相关章节时记录警告，但不得编造设计事实。
- 调度 slot agent 前，先要求其识别当前 slot 的责任闭环：业务能力、接口能力、页面主流程、组件族、测试资产闭环或验收闭环；技术层、文件类型和实现步骤只作为拆分的辅助线索。
- 按当前阶段 slot 串行调度相应 agent。每个 slot agent 必须按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 通过 `Agent` tool 启动，`subagent_type` 按 Agent Dispatch Mapping 映射。
- 传入 agent prompt 的内容保持精简：阶段设计摘要、上游 handoff、目标 guide/protocol 路径、责任闭环识别要求、输出字段要求、`needs_user_answer` 规则；不得复制 guide、protocol 或 agent 文档中的长篇规则。
- 生成 backend/test runner item 时，必须要求 agent 从 `Expected Test Manifest`、变更文件和 package/module/test name 推导最小可靠定向命令；不得把全量 `uv run scripts/backend-test.py --` 作为默认 runner validation。
- slot agent 返回结构统一参考 [Agent Output Contract](#agent-output-contract)。
- 主流程在每个 slot 返回后先执行写入前硬校验：
   - item 必填字段齐备
   - item ID 唯一
   - manifest 按返回的 items 顺序覆盖全部 items，路径与 item 文件一致
   - 符合 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 和 `${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md` 的 P0/P1 硬门禁
   - backend/test runner 若使用全量 `uv run scripts/backend-test.py --`，必须在 `Validation` 或 `Handoff` 写明无法可靠定向的具体原因或门禁要求；否则拒绝写入成功状态
- 硬校验失败时终止当前 slot，不写入成功状态，要求重新生成该 slot。
- 硬校验通过后写入当前 slot manifest 和 item 文件，再继续调用下游 slot。
- 当前阶段 slot 齐备后生成 `<phase>/index.md`，用 `Decision ID | Status | Task/Item Location | Notes` 表追踪影响当前 phase 的 Active Decision。
- 收集当前 phase 的 `index.md`、slot manifest 和 item Markdown，运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py <all-phase-markdown-paths>`；命中项按 Decision Exposure Gate 处理，重新扫描通过前不得交付任务计划。
- 写入或更新 `.state.json`：当前 phase 新生成且尚未执行的 item 写为 `generated`，再按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md` 聚合 slot 和 phase；不得在 `/t-task` 中提前改为 `pending`。
- 返回下一步建议：复杂或高风险任务先运行 `/t-task-check [feature] --phase [phase]`；简单任务可直接运行 `/t-run [feature] --phase [phase]`。

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
| flutter | dev | flutter-dev |
| flutter | test | flutter-test |
| flutter | accept | flutter-accept |
| web-demo | dev | web-demo-dev |
| web-demo | accept | web-demo-accept |
| flutter-demo | dev | flutter-demo-dev |
| flutter-demo | accept | flutter-demo-accept |

## Slot Manifest Contract
每个 slot manifest 必须包含：
- slot 目标和边界
- item 表格：`id | title | agent | file`；表格从上到下即 `/t-run` 执行顺序
- 必要的上游输入和下游 handoff 摘要

manifest 不得包含完整实现步骤；完整步骤必须写入 item 文件。

## Generated Document Style

任务文档面向 `/t-run` 执行，不承载教程或指南复述：

- 只写当前 feature、phase、slot、item 的可执行事实。
- 引用 guide、protocol、agent 文档路径，不复制其中的长篇规则。
- item 正文只使用 `Goal / Work / Files / Validation / Handoff` 五个章节。
- `Work` 写具体动作，不写通用工程原则。
- `Validation` 写目标项目真实命令、脚本或验收证据，不写抽象测试建议。
- item 应写明失败边界：失败时定位到哪类问题、由哪个 agent/slot 继续处理。
- `Handoff` 只保留给顺序中后续 slot/agent 必需的信息；没有交接内容时写 `None`。
- 受具体决定约束的 item 在 `Goal` 或 `Handoff` 引用稳定 DEC ID，不复制整条决策历史。

## Agent Output Contract
slot agent 输出必须至少包含：
- `slot`: `dev|test|accept`
- `manifest_target_file`
- `manifest_content`
- `items`: 按执行顺序排列的 item 对象列表，每个 item 包含 `id/file/agent/content`
- `self_check`: 必填字段、执行顺序、责任闭环拆分、过度拆分、阶段执行规则和 P0/P1 风险自检结果

主流程必须：
- 校验 `slot` 与被调度 agent 是否匹配。
- 校验 manifest 表格顺序与 `items` 列表一致，且 manifest、item 文件路径和 `.state.json` 计划一致。
- 校验 item 使用 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的最小结构。
- 校验 `self_check` 存在且未声明未解决 P0/P1。
- 校验 slot agent 已说明 item 的责任闭环；若存在把技术层、文件类型或实现步骤当成唯一拆分依据、重复验证命令或不可独立验收的过度拆分，拒绝写入成功状态。
- 校验 slot item 数量上限；超限时必须具有用户授权证据，否则拒绝写入。
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
- 当前阶段 slot 并行生成；slot 必须按固定顺序串行。
- 未写入上游 manifest 和 item 文件就调用下游 slot agent。
- 在任务文档中复制 guide/protocol/subagent 的长篇指南。
- 在 item 中写与当前交付无关的通用实现建议、培训内容或风格偏好。
- 违反 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的拆分、测试集中执行或 backend/test runner 规则。
- backend/test runner 默认规划全量 `uv run scripts/backend-test.py --`，却没有证明定向范围无法可靠覆盖或存在明确门禁要求。

## Failure
- 设计文档不存在：提示先运行 `/t-design [feature]`。
- 任一 slot agent 生成失败：终止本次任务生成，不写入该 slot 的成功状态，并返回失败 agent 与失败原因。
- slot agent 返回 item 缺少必填字段，或 manifest 顺序与 items 列表不一致：拒绝写入成功状态，要求重新生成该 slot。
- slot agent 返回缺失 `self_check`、manifest 覆盖不完整、backend/test 类型非法、触发必须拆分规则、明显过度拆分，或 item 数量超限且无用户授权证据：拒绝写入成功状态，要求重新生成或合并该 slot。
- slot agent 返回 `needs_user_answer`：使用 `AskUserQuestion` 向用户提问，回答前不写入该 slot；回答后先同步设计/规划依据，再重新生成该 slot。

## Examples
```bash
# 生成 backend 阶段任务
/t-task <feature> --phase backend

# 未指定 phase 时选择第一个 active phase
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
下一步: 可选运行 /t-task-check <feature> --phase backend；或直接 /t-run <feature> --phase backend
```
