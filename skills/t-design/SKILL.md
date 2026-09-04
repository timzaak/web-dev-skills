---
name: t-design
description: Generate technical design documents including API design, database schema, and implementation details for a feature.
argument-hint: "[方案名称]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Task
  - Agent
  - Write
  - Bash
---

# 技术设计文档生成

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（判断产物写入位置或项目事实与插件默认冲突时读）
需求来源边界：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`（区分草稿与已发布需求来源、处理两者并存裁决时读）
决策连续性和用户决策暴露：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`（提问、更新决策账本或处理决策暴露门禁时读）
子 agent 调用：`${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`（调度设计 agent 前 read 其对应角色规范）
设计 agent 输出：`${CLAUDE_PLUGIN_ROOT}/protocols/design-agent-output-contract.md`（解析 subagent 返回前读）
设计生成状态：`${CLAUDE_PLUGIN_ROOT}/protocols/design-state-contract.md`（写入或校验 `.state.json` 时读）

设计生成应保持简单、当前必需、可追溯；如果需求、spec、代码或本 skill 冲突，停止并说明冲突。

需要用户裁决的设计缺口必须通过 `AskUserQuestion` 解决，不得只写入风险、待确认事项或假设后继续生成。

## 适用范围

仅在以下场景使用：
- 用户明确要求"技术设计""方案设计""架构设计""API 设计""数据模型设计"
- 用户明确执行 `/t-design [方案名称]`
- 已经确认这是新功能或较大能力扩展，需要正式设计文档进入 DDD 流程

不要因为用户只是问"怎么实现""大概怎么做"就自动触发本 skill。

## 目标

基于用户故事、PRD 草稿、已发布 PRD 基线、技术预研、用户已准备的仓库内资料和现有代码，生成可实施、可追踪、可用于 `/t-task` 的技术设计。`/t-prd-check` 是推荐的可选上游检查；未运行时，本 skill 必须自行完成关键需求来源混合验证。

后端、前端、Flutter 的着重点不同，设计拆分为一份主文档加按端拆分的分端设计文档；每个适用端由对应设计 subagent 生成，主会话负责编排、跨端裁决和汇总。输出文件见 Output Contract。

不适用端不创建分端文档，只在主文档 §4.2 标记"不适用"及原因。

如果未传方案名称，立即终止并提示：
`请提供方案名称。例如：/t-design <feature>`

## Input Contract

上游输入（按设计类型选择；读取顺序：先索引，再 `.ai/decision` / `.ai/decision-log`，再需求来源，最后 guides）：
- 业务功能设计：
  - `.ai/decision/<feature>.md` — 产品立项决策简报（如存在，作为 PRD 之前的方向约束）
  - `.ai/decision-log/<feature>.md` — 跨阶段决策账本（存在时必须读取）
  - `.ai/prd/<domain>/<feature>.md` — PRD 草稿（如存在，作为当前候选需求）
  - `docs/prd/<domain>/<feature>.md` — 已发布 PRD 基线（如存在，作为正式需求基线）
  - `.ai/user-stories/**/*.md` — draft 用户故事（如存在，作为当前候选需求）
  - `docs/user-stories/**/*.md` — 已发布相关用户故事
  - `docs/prd/00-index.md`、`docs/user-stories/00-index.md` — 索引
- 纯技术方案设计：
  - `.ai/tech-research/<feature>.md` — 技术预研报告，可作为唯一上游需求来源
  - 仅适用于不涉及业务逻辑、产品规则、用户可见流程或验收目标变动的设计

可选输入：
- `${CLAUDE_PLUGIN_ROOT}/guides/core/environment-and-testing-guide.md` — 环境与测试指南
- `${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md` — 后端开发规范
- `${CLAUDE_PLUGIN_ROOT}/guides/frontend/development.md` — 前端开发规范
- `${CLAUDE_PLUGIN_ROOT}/guides/flutter/development.md` — Flutter 开发规范（目标项目启用 Flutter 时）
- `${CLAUDE_PLUGIN_ROOT}/guides/flutter/demo-testing.md` — Android Patrol 用户故事演示规范（设计要求 Flutter Demo 时）
- `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md` — 质量规范

## Output Contract

下游产出：
- `.ai/design/$ARGUMENTS.md` — 设计主文档，包含：
  - 目标与范围
  - 用户故事/PRD/技术预研引用与完整 Decision Trace
  - 跨端现状概览
  - 总体设计与关键取舍、交付端范围
  - 跨端契约（API 契约摘要与契约源声明）
  - 分端设计摘要
  - 测试与验收策略（跨端汇总）
  - 风险与验证动作（汇总）
  - 文件影响范围（全量汇总，`/t-task` 的唯一拆分依据）
- `.ai/design/$ARGUMENTS/backend.md` — 后端分端设计（适用时），包含 API 契约（唯一设计源）、数据库设计、领域逻辑、权限安全、详细设计、后端测试策略
- `.ai/design/$ARGUMENTS/frontend.md` — 前端分端设计（适用时），包含页面/组件/线框、状态与数据流、交互与关键状态、性能、测试与 Demo 策略
- `.ai/design/$ARGUMENTS/flutter.md` — Flutter 分端设计（适用时），包含分层架构、状态管理、页面与导航、可测试性、测试与 Patrol Demo 策略
- `.ai/design/$ARGUMENTS/.state.json` — 设计生成状态；结构见 `${CLAUDE_PLUGIN_ROOT}/protocols/design-state-contract.md`，只有 `complete` 可被下游消费
- `.ai/decision-log/$ARGUMENTS.md` — 复用上游决策；仅在产生用户决策、问题状态变化或重要 AI 决策时更新

## 核心约束

- 业务功能设计必须混合验证 `.ai/prd` 草稿与 `docs/prd` 正式 PRD、`.ai/user-stories` draft 与 `docs/user-stories` 已发布故事；并存时的裁决规则（一致/增量继续、冲突停止、无草稿用基线、默认基于草稿）统一按 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` 的"同一 feature 草稿与正式来源并存的裁决"执行
- 若存在 `.ai/decision/<feature>.md`，设计必须尊重其中目标用户、Scope Direction、D0/D1 产品决策和 Handoff；不得用技术方案静默改变立项结论
- 若存在 `.ai/decision-log/<feature>.md`，必须逐项承接影响设计的 Active Decision；不得重复询问 Resolved Question，也不得使用 Superseded Decision
- 纯技术方案没有 PRD/用户故事时，以 `.ai/tech-research/<feature>.md` 中的技术目标、约束和影响范围为准；必须在主文档中声明"纯技术方案设计，不涉及业务逻辑变动"，并引用对应技术预研报告；执行流程与质量门禁以 `${CLAUDE_PLUGIN_ROOT}/guides/` 为准
- 只引用用户故事，不粘贴完整故事正文或整段 Gherkin
- 优先复用现有实现，不凭空设计新架构
- 默认不搜索额外资料；人类在进入 `/t-design` 前应已准备好相关资料。只有在人类明确要求补充外部依据时，才可将外部资料作为附加参考
- API 契约的单一设计源是 backend 分端文档；frontend/flutter 分端文档只声明依赖的接口与字段，不得复制或另立契约；后端不适用时以现有 OpenAPI/SDK 或接口为契约源
- 主文档不承载 API 字段表、数据库表结构和页面线框等分端细节；细节只活在对应分端文档，主文档保留摘要与链接
- 数据库设计遵循"尽量简洁、当前必需、避免过度审计设计"
- 现状依据及 MODIFY/DELETE 路径必须真实存在；CREATE 路径可以尚不存在，但父目录必须真实存在，并给出相邻实现或项目规范作为命名依据
- 分端文档由对应设计 subagent 生成；主会话不得绕过 subagent 代写分端设计，除非该端不适用

## 工作流程

### 1. 验证参数和输出位置

- 校验 `$ARGUMENTS` 非空
- 文件名仅允许中文、英文、数字、空格、下划线、连字符

如果 `.ai/design/$ARGUMENTS.md` 或 `.ai/design/$ARGUMENTS/` 下任一分端文档已存在，先询问是否覆盖。

用户确认覆盖后，先重新判定适用端，删除上一轮存在但本轮不适用的分端文档。调度前按输出协议写入 `.ai/design/$ARGUMENTS/.state.json`，状态为 `in_progress`。

### 2. 收集最小必要输入

如果当前上下文里还没有足够信息，使用 `AskUserQuestion` 只补齐以下内容：
- 功能目标或问题陈述
- 人类已准备好的相关资料路径或名称
- 需要覆盖的范围边界
- 交付端范围（仅当无法从需求来源、现有代码或 Decision Log 判断时）

如果用户已经在当前对话或命令参数里给出足够信息，不要重复提问。

提问前必须按 Topic 检查 Decision Log 的 Active Decisions、Resolved Questions 和 Deferred Questions。若已有结论，直接采用；只有出现新冲突证据或满足重开条件时才能重新提问。

若缺失或冲突会影响目标范围、业务规则、权限/安全边界、API 契约、数据模型、迁移/兼容性、验收标准、显著成本、风险接受或测试策略，必须在继续设计前使用 `AskUserQuestion` 获取答案；不得把它写入风险、验证动作或假设后继续。

用户回答后，先更新 Decision Log，再更新对应产物。D2 工程取舍由设计阶段明确选择并写入 Design；符合 Decision Continuity Contract 的 Entry Gate 时才回写 Decision Log。

### 3. 搜索需求来源

只搜索真实目录：
- `docs/user-stories/**/*.md`
- `.ai/user-stories/**/*.md`
- `.ai/prd/**/*.md`
- `docs/prd/**/*.md`
- `.ai/tech-research/**/*.md`
- `docs/design/**/*.md`、`.ai/design/**/*.md`（如果存在相关先例）

优先做法：先从索引定位候选文档，再对候选文档做 `Grep`，最后 `Read` 真正相关的少量文件。

业务功能设计至少提取：用户故事 ID/标题/优先级/来源文件、场景概述或验收目标摘要、PRD 草稿中的当前候选业务边界/规则/非功能要求、已发布 PRD 基线及草稿相对基线的差异、draft 用户故事相对已发布故事的新增或变更场景、Decision Log 中影响设计的 Active Decisions / 已解决问题 / 本阶段到期的 Deferred Questions。

草稿与正式 PRD、draft 与已发布用户故事的并存处理按核心约束引用的裁决规则执行；冲突无法确认覆盖关系时停止并提示修正草稿，必要时运行 `/t-prd-check [feature]`。

如果没有找到足够的用户故事或 PRD：
- 优先检查是否存在 `.ai/tech-research/$ARGUMENTS.md`
- 如果存在且内容足以支撑纯技术方案，继续生成设计，并在需求来源中标记 PRD/用户故事不适用
- 如果不存在或技术预研不足，且缺失会影响方案判断，使用 `AskUserQuestion` 要求用户补齐目标、范围或来源后再继续
- 只有不需要用户选择、且不影响方案方向、实现边界和验收结论的证据限制，才可在设计文档中记录为"已确认假设与证据限制"

纯技术方案设计至少提取：技术目标、当前约束、选定技术路线、依赖或版本变化、影响范围、风险和不涉及业务逻辑变动的边界声明。

### 4. 分析现有实现

分析真实代码结构，不要假设，需要输出：
- 现有实现入口（后端、前端、Flutter 各自的现状）
- 可复用模块
- 需要修改的边界
- 与当前架构或约束冲突的点

如果代码分析较复杂，使用 `Task` 启动 Explore agent，给出清晰任务：
- 找出现有实现位置
- 标出可复用点
- 标出最可能受影响的模块
- 返回具体文件路径和理由

### 5. 确定交付端范围与契约归属

判定 backend / frontend / flutter 哪些端适用：
- 依据需求来源中的交付端描述、`${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的 phase 结构、现有代码结构（如 `frontend/`、Flutter 工程是否存在）和 Decision Log
- 判定结果影响拆分方向且无法确定时，使用 `AskUserQuestion` 确认

契约归属：
- backend 适用时，API 契约由 backend 分端设计产出，backend 设计必须先行
- backend 不适用时，契约源为现有实现分析中确认的现有接口/OpenAPI/SDK，frontend/flutter 可直接并行生成

在主文档 §4.2 记录交付端范围和判定依据。

### 6. 分端生成设计（subagent 编排）

按适用端调度设计 agent，`subagent_type` 映射：

| 端 | subagent_type | 模板 | 输出 |
|---|---|---|---|
| backend | backend-design | [template-backend.md](${CLAUDE_PLUGIN_ROOT}/skills/t-design/template-backend.md) | `.ai/design/$ARGUMENTS/backend.md` |
| frontend | frontend-design | [template-frontend.md](${CLAUDE_PLUGIN_ROOT}/skills/t-design/template-frontend.md) | `.ai/design/$ARGUMENTS/frontend.md` |
| flutter | flutter-design | [template-flutter.md](${CLAUDE_PLUGIN_ROOT}/skills/t-design/template-flutter.md) | `.ai/design/$ARGUMENTS/flutter.md` |

调度顺序：
- backend 适用 → 先调度 backend-design，成功后再调度 frontend-design / flutter-design
- backend 不适用 → frontend-design / flutter-design 可并行调度
- 同一批次内同一角色复用按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 的同批次同角色复用规则执行

每次调度前必须：
- 按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` Read 对应 `agents/<role>.md` 全文并注入为子 agent prompt 的角色指令段
- 在 prompt 中提供最小上下文：
  - 方案名与输出路径
  - 需求来源文件路径清单（用户故事/PRD/技术预研）与关键摘要
  - Decision Log 路径及影响本端的 Active Decision 摘要
  - 现有实现分析结论（本端相关部分）
  - 契约源：backend 适用时传 `.ai/design/$ARGUMENTS/backend.md` 路径及 `design_result.contract_summary`；否则传现有接口清单
  - 分端模板路径（按上方映射表传入对应 template 文件）与对应 guide 路径
  - `${CLAUDE_PLUGIN_ROOT}/protocols/design-agent-output-contract.md`
- 不复制 guide、protocol 或 agent 文档中的长篇规则

处理子 agent 返回：
- 只读取 `task_completion.status` 和 `design_result`，拒绝旧的顶层 `status/doc_path/contract_summary` 返回结构
- `design_result.needs_user_answer` 非空 → 按 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` 检查 Decision Log；仍未解决时使用 `AskUserQuestion` 向用户提问，回答后先更新 Decision Log，再重新调度该端
- `task_completion.status=partial` 或 `design_result.self_check` 未通过 → 不进入合并；修复输入后重新调度，无法恢复时把生成状态写为 `failed`
- `task_completion.status=failed` → 终止该端并把生成状态写为 `failed`；不得写入该端成功状态
- frontend/flutter 的 `design_result.contract_dependencies` 必须按输出协议逐项对比 backend 的 `design_result.contract_summary`；operation、method/path、字段子集或调用方冲突时重新调度客户端设计，属于产品语义冲突时使用 `AskUserQuestion` 裁决
- 每个端成功后更新 `completed_stacks`；全部适用端 `task_completion.status=success` 后进入合并

### 7. 合并生成主文档

使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-design/template.md) 生成 `.ai/design/$ARGUMENTS.md`，内容来自前序步骤与各分端文档返回：

- 目标、范围、需求来源与完整 Decision Trace（主会话编写；分端文档只保留本端 DEC 子集）
- 跨端现状概览、总体设计与关键取舍、交付端范围
- 跨端契约摘要（来自 backend `design_result.contract_summary` 或现有接口）与契约源声明
- 分端设计摘要（来自各端 `task_completion.summary`，每端 3-5 行）
- 测试与验收策略跨端汇总（来自各分端文档测试章节）
- 风险与验证动作汇总
- §8 文件影响范围：逐行合并各分端文档的文件影响表，标注来源分端；此表是 `/t-task` 的唯一拆分依据，必须覆盖全部适用端

如果某章节不适用，保留章节并标记"不适用"及原因。

写入后对所有设计文档运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py ".ai/design/$ARGUMENTS.md" ".ai/design/$ARGUMENTS/backend.md" ".ai/design/$ARGUMENTS/frontend.md" ".ai/design/$ARGUMENTS/flutter.md"
```

（仅扫描实际生成的文档。）

扫描命中时按 Decision Exposure Gate 分类并处理；重新扫描通过前不得交付设计或建议进入 `/t-task`。

随后运行确定性结构校验：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-design.py ".ai/design/$ARGUMENTS.md"
```

结构校验检查章节、模板占位符、适用端文档、契约 operation、文件影响汇总和路径操作。两项扫描全部通过后，才把 `.state.json` 写为 `complete`。

高风险、跨端或长文档设计在完成前额外调度一个无原会话背景的通用只读 agent，只提供全部设计文档和以下问题：实现入口、契约唯一来源、失败/权限/兼容路径、测试入口、文件影响范围。若读者无法从文档稳定回答或发现矛盾，修正文档并重新执行两项扫描；简单设计跳过时在收尾说明。

### 8. 分端设计要求

逐项按对应 `agents/*-design.md` 的"着重点"和质量清单验收。额外拒绝以下结果：

- API 缺少 operation ID、字段语义或具体契约源。
- frontend/flutter 复制 API 字段定义，或客户端状态方案偏离对应 guide。
- CREATE 路径缺少父目录和命名依据；MODIFY/DELETE 路径不存在。
- 风险仍包含需要用户裁决的问题。

### 9. 收尾输出

完成后在响应中明确说明：
- 主文档与各分端文档路径
- Decision Log 路径和本轮新增/复用/替代的 DEC/Q ID
- 本次设计覆盖的核心范围与适用端
- 关键风险和验证动作
- 无上下文读者测试：`passed` 或 `skipped` 及原因
- 延期问题：明确说明"无"，或列出已告知用户、写入 Decision Log 且尚未到最迟解决阶段的 Q ID
- 下一步命令：高风险或复杂设计建议运行 `/t-design-check $ARGUMENTS`；简单设计可直接进入 `/t-task $ARGUMENTS`
- 如文档内容较多或结构复杂，可使用 `/t-html-show .ai/design/$ARGUMENTS.md` 生成 HTML 可视化预览

## 质量检查清单

交付前确认：

- 需求来源混合验证完成；纯技术方案已声明业务边界。
- 设计复用现有架构，没有未解释的新抽象。
- 每个适用端均由对应 agent 生成并通过其质量清单。
- 主文档覆盖全部 Active Decision、Requirement/Story 和分端文件影响。
- `needs_user_answer=0`。
- `check-decision-closure.py` 与 `check-design.py` 通过。
- `.state.json` 已写为 `complete`。

## 失败处理

- 参数缺失：终止并给出 `/t-design [方案名称]` 示例
- 文件名非法：终止并说明允许字符范围
- 无法创建输出目录或写文件：终止并报告
- 未找到足够需求文档：若影响设计判断，使用 `AskUserQuestion` 补齐并停止；不影响时只记录不需要用户选择的证据限制
- 子 agent 返回 `needs_user_answer`：按 Topic 查 Decision Log；未解决时提问并停止，回答后更新 Decision Log 并重新调度该端
- 子 agent 返回 `partial`、失败或超时：允许继续收集其他端诊断，但不得合并主文档；无法在本轮恢复时把 `.state.json` 写为 `failed` 并报告失败 agent 与原因
- 跨端契约冲突：以 backend 契约为准修正客户端分端设计；产品语义级冲突升级为 `AskUserQuestion`
- 决策闭合扫描失败：按 Decision Exposure Gate 分类；需要用户裁决时提问并停止，修正后重新扫描
- 代码分析失败：继续，但标记"现有实现分析不完整"
