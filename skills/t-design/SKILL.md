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

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
需求来源边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`
跨阶段决策连续性和用户决策暴露统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`
子 agent 调用规范统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`

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

后端、前端、Flutter 的着重点不同，设计拆分为一份主文档加按端拆分的分端设计文档；每个适用端由对应设计 subagent 生成，主会话负责编排、跨端裁决和汇总。

输出文件：
- `.ai/design/$ARGUMENTS.md` — 主文档：目标范围、需求来源、跨端契约、测试与风险汇总、全量文件影响范围
- `.ai/design/$ARGUMENTS/backend.md` — 后端分端设计（适用时）
- `.ai/design/$ARGUMENTS/frontend.md` — 前端分端设计（适用时）
- `.ai/design/$ARGUMENTS/flutter.md` — Flutter 分端设计（适用时）
- `.ai/decision-log/$ARGUMENTS.md` — 复用上游决策并记录本阶段新 D2 决策或已解决问题

不适用端不创建分端文档，只在主文档 §4.2 标记"不适用"及原因。

如果未传方案名称，立即终止并提示：
`请提供方案名称。例如：/t-design <feature>`

## Input Contract

上游输入（按设计类型选择）：
- 业务功能设计：
  - `.ai/decision/<feature>.md` — 产品立项决策简报（如存在，作为 PRD 之前的方向约束）
  - `.ai/decision-log/<feature>.md` — 跨阶段决策账本（存在时必须读取）
  - `.ai/prd/<domain>/<feature>.md` — PRD 草稿（如存在，作为当前候选需求）
  - `docs/prd/<domain>/<feature>.md` — 已发布 PRD 基线（如存在，作为正式需求基线）
  - `.ai/user-stories/**/*.md` — draft 用户故事（如存在，作为当前候选需求）
  - `docs/user-stories/**/*.md` — 已发布相关用户故事
  - `docs/prd/00-index.md` — PRD 索引
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

## 核心约束

- 业务功能设计必须混合验证 `.ai/prd` 草稿与 `docs/prd` 正式 PRD：草稿是当前候选需求，正式 PRD 是已发布基线；两者存在未说明冲突时停止并要求修正草稿，必要时运行 `/t-prd-check [feature]`
- 业务功能设计必须混合验证 `.ai/user-stories` draft 与 `docs/user-stories` 已发布故事：draft story 是当前候选需求，正式 story 是已发布基线；两者存在未说明冲突时停止并要求修正草稿，必要时运行 `/t-prd-check [feature]`
- 若存在 `.ai/decision/<feature>.md`，设计必须尊重其中目标用户、Scope Direction、D0/D1 产品决策和 Handoff；不得用技术方案静默改变立项结论
- 若存在 `.ai/decision-log/<feature>.md`，必须逐项承接影响设计的 Active Decision；不得重复询问 Resolved Question，也不得使用 Superseded Decision
- 若存在 `.ai/prd` 草稿且内容会影响设计，默认基于草稿继续设计，并在设计文档中标记是否已找到对应 PRD Check 报告；不得要求先发布到 `docs/prd`
- 若存在 `.ai/user-stories` draft 且内容会影响设计，默认基于 draft story 继续设计，并在设计文档中保留 `.ai/user-stories/...` 来源路径；不得要求先发布到 `docs/user-stories`
- 若没有 `.ai/prd` 草稿但存在 `docs/prd` 正式 PRD，可基于正式 PRD 继续设计，并在设计文档中标记"未发现 PRD 草稿"
- 纯技术方案没有 PRD/用户故事时，以 `.ai/tech-research/<feature>.md` 中的技术目标、约束和影响范围为准；执行流程与质量门禁以 `${CLAUDE_PLUGIN_ROOT}/guides/` 为准
- 没有 PRD/用户故事时，必须在主文档中声明"纯技术方案设计，不涉及业务逻辑变动"，并引用对应 `.ai/tech-research/<feature>.md`
- 先读索引，再读相关明细
- 只引用用户故事，不粘贴完整故事正文或整段 Gherkin
- 优先复用现有实现，不凭空设计新架构
- 默认不搜索额外资料；人类在进入 `/t-design` 前应已准备好相关资料
- 只有在人类明确要求补充外部依据时，才可将外部资料作为附加参考
- API 契约的单一设计源是 backend 分端文档；frontend/flutter 分端文档只声明依赖的接口与字段，不得复制或另立契约；后端不适用时以现有 OpenAPI/SDK 或接口为契约源
- 主文档不承载 API 字段表、数据库表结构和页面线框等分端细节；细节只活在对应分端文档，主文档保留摘要与链接
- 数据库设计遵循"尽量简洁、当前必需、避免过度审计设计"
- 文档中的文件路径必须使用仓库真实路径，不允许使用不存在的示例路径
- 分端文档由对应设计 subagent 生成；主会话不得绕过 subagent 代写分端设计，除非该端不适用

## 先读这些文件

按以下顺序建立上下文：
- `docs/user-stories/00-index.md`
- `.ai/user-stories/$ARGUMENTS.md` 或 `.ai/user-stories/**/$ARGUMENTS.md`（如存在）
- `docs/prd/00-index.md`
- `.ai/decision/$ARGUMENTS.md`（如存在）
- `.ai/decision-log/$ARGUMENTS.md`（如存在；必须在任何提问之前读取）
- `.ai/prd/$ARGUMENTS.md` 或 `.ai/prd/**/$ARGUMENTS.md`（如存在）
- `docs/prd/**/$ARGUMENTS.md`（如存在）
- `.ai/tech-research/$ARGUMENTS.md`（如存在）
- `${CLAUDE_PLUGIN_ROOT}/guides/core/environment-and-testing-guide.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md`、`${CLAUDE_PLUGIN_ROOT}/guides/frontend/development.md` 和/或 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/development.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md`

## 工作流程

### 1. 验证参数和输出位置

- 校验 `$ARGUMENTS` 非空
- 文件名仅允许中文、英文、数字、空格、下划线、连字符

如果 `.ai/design/$ARGUMENTS.md` 或 `.ai/design/$ARGUMENTS/` 下任一分端文档已存在，先询问是否覆盖。

### 2. 收集最小必要输入

如果当前上下文里还没有足够信息，使用 `AskUserQuestion` 只补齐以下内容：
- 功能目标或问题陈述
- 人类已准备好的相关资料路径或名称
- 需要覆盖的范围边界
- 交付端范围（仅当无法从需求来源、现有代码或 Decision Log 判断时）

如果用户已经在当前对话或命令参数里给出足够信息，不要重复提问。

提问前必须按 Topic 检查 Decision Log 的 Active Decisions、Resolved Questions 和 Deferred Questions。若已有结论，直接采用；只有出现新冲突证据或满足重开条件时才能重新提问。

若缺失或冲突会影响目标范围、业务规则、权限/安全边界、API 契约、数据模型、迁移/兼容性、验收标准、显著成本、风险接受或测试策略，必须在继续设计前使用 `AskUserQuestion` 获取答案；不得把它写入风险、验证动作或假设后继续。

用户回答后，先更新 Decision Log，再更新拥有该事实的 PRD、Tech Research 或 Design。D2 工程取舍若不改变产品语义、风险接受、显著成本或兼容承诺，由设计阶段明确选择并记录 DEC，不得写成“待确认”。

### 3. 搜索需求来源

只搜索真实目录：
- `docs/user-stories/**/*.md`
- `.ai/user-stories/**/*.md`
- `.ai/prd/**/*.md`
- `docs/prd/**/*.md`
- `.ai/tech-research/**/*.md`
- `docs/design/**/*.md`（如果存在相关先例）
- `.ai/design/**/*.md`（如果存在相关先例）

优先做法：
- 先从索引定位候选文档
- 再对候选文档做 `Grep`
- 最后 `Read` 真正相关的少量文件

业务功能设计至少提取这些内容：
- 用户故事 ID、标题、优先级、来源文件
- 场景概述或验收目标的简短摘要
- PRD 草稿中的当前候选业务边界、规则、非功能要求
- 已发布 PRD 中的正式基线，以及草稿相对基线的目标、范围、规则、状态和验收目标差异
- draft 用户故事相对已发布故事的新增或变更场景，以及未说明冲突
- Decision Log 中影响设计的 Active Decisions、已解决问题和本阶段到期的 Deferred Questions

如果同时存在草稿和正式 PRD：
- 草稿与正式 PRD 一致或明确是增量/替换 → 继续设计，并在"需求来源"中同时引用两者和差异摘要
- 草稿与正式 PRD 在核心业务边界、权限规则或验收目标上冲突，且无法从草稿确认覆盖关系 → 停止并提示修正草稿，必要时运行 `/t-prd-check [feature]`

如果同时存在 draft 用户故事和已发布用户故事：
- draft story 与已发布 story 一致或明确是增量/替换 → 继续设计，并在"需求来源"中同时引用两者和差异摘要
- draft story 与已发布 story 在核心角色、权限规则或验收目标上冲突，且无法确认覆盖关系 → 停止并提示修正 draft story，必要时运行 `/t-prd-check [feature]`

如果没有找到足够的用户故事或 PRD：
- 优先检查是否存在 `.ai/tech-research/$ARGUMENTS.md`
- 如果存在且内容足以支撑纯技术方案，继续生成设计，并在需求来源中标记 PRD/用户故事不适用
- 如果不存在或技术预研不足，且缺失会影响方案判断，使用 `AskUserQuestion` 要求用户补齐目标、范围或来源后再继续
- 只有不需要用户选择、且不影响方案方向、实现边界和验收结论的证据限制，才可在设计文档中记录为“已确认假设与证据限制”

纯技术方案设计至少提取这些内容：
- 技术目标、当前约束、选定技术路线
- 依赖或版本变化
- 影响范围、风险和不涉及业务逻辑变动的边界声明

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
  - 契约源：backend 适用时传 `.ai/design/$ARGUMENTS/backend.md` 路径及 `contract_summary`；否则传现有接口清单
  - 分端模板路径（按上方映射表传入对应 template 文件）与对应 guide 路径
- 不复制 guide、protocol 或 agent 文档中的长篇规则

处理子 agent 返回：
- `needs_user_answer` 非空 → 按 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` 检查 Decision Log；仍未解决时使用 `AskUserQuestion` 向用户提问，回答后先更新 Decision Log，再重新调度该端
- `status=failed` → 终止该端并报告失败原因；不得写入该端成功状态
- frontend/flutter 的 `contract_dependencies` 与 backend `contract_summary` 冲突（字段缺失、路径不一致）→ 以 backend 契约为准，修正客户端端设计后重新调度该端；属于产品语义冲突时使用 `AskUserQuestion` 裁决
- 全部适用端 `status=success` 后进入合并

### 7. 合并生成主文档

使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-design/template.md) 生成 `.ai/design/$ARGUMENTS.md`，内容来自前序步骤与各分端文档返回：

- 目标、范围、需求来源与完整 Decision Trace（主会话编写；分端文档只保留本端 DEC 子集）
- 跨端现状概览、总体设计与关键取舍、交付端范围
- 跨端契约摘要（来自 backend `contract_summary` 或现有接口）与契约源声明
- 分端设计摘要（来自各端 `summary`，每端 3-5 行）
- 测试与验收策略跨端汇总（来自各分端文档测试章节）
- 风险与验证动作汇总
- §8 文件影响范围：逐行合并各分端文档的文件影响表，标注来源分端；此表是 `/t-task` 的唯一拆分依据，必须覆盖全部适用端

如果某章节不适用，保留章节并标记"不适用"及原因。

写入后对所有设计文档运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py .ai/design/$ARGUMENTS.md .ai/design/$ARGUMENTS/backend.md .ai/design/$ARGUMENTS/frontend.md .ai/design/$ARGUMENTS/flutter.md
```

（仅扫描实际生成的文档。）

扫描命中时按 Decision Exposure Gate 分类并处理；重新扫描通过前不得交付设计或建议进入 `/t-task`。

### 8. 分端设计要求

各端深度要求的单一事实源是 `${CLAUDE_PLUGIN_ROOT}/agents/backend-design.md`、`${CLAUDE_PLUGIN_ROOT}/agents/frontend-design.md` 和 `${CLAUDE_PLUGIN_ROOT}/agents/flutter-design.md` 的"着重点"章节；主会话在合并时按以下底线验收，不在此复制完整清单：

- backend：API 接口清单五要素齐全（方法、路径、用途、权限/身份、调用方）；关键接口有请求/响应字段与错误响应；DTO 新增/复用边界与 OpenAPI/SDK 关系明确；数据库设计可建表/可迁移且有迁移策略；领域逻辑覆盖核心规则、校验、事务与幂等
- frontend：涉及用户可见交互时以用户体验描述为主（入口、操作路径、系统反馈、默认值、错误状态与恢复），技术实现只做承载体验所需的最小映射；页面/路由/组件清单与层级边界明确；状态分工遵循 TanStack Query（服务端数据）/ Zustand（客户端 UI 状态）约定，服务端数据不复制进 store；API 依赖只引用契约源；不规定具体 props/state 细节
- flutter：涉及用户可见交互时以用户体验描述为主，技术实现只做最小映射；UI/data 分层职责与数据流向明确（不过度分层）；状态管理遵循 Riverpod 技术线（以 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/constitution.md` 为准），notifier 划分、生命周期与订阅范围明确；页面与导航承接明确；依赖注入与可测试边界明确
- 所有端：只记录方向已确定的风险；文件路径为仓库真实路径

禁止：
- 只给示例 JSON，不说明字段含义
- 只写"复用现有接口"但不指出具体路径或边界
- 使用与仓库规范冲突的 snake_case 路径参数
- 在 frontend/flutter 分端文档中单列或复制 API 契约字段表

### 9. 收尾输出

完成后在响应中明确说明：
- 主文档与各分端文档路径
- Decision Log 路径和本轮新增/复用/替代的 DEC/Q ID
- 本次设计覆盖的核心范围与适用端
- 关键风险和验证动作
- 延期问题：明确说明“无”，或列出已告知用户、写入 Decision Log 且尚未到最迟解决阶段的 Q ID
- 下一步命令：高风险或复杂设计建议运行 `/t-design-check $ARGUMENTS`；简单设计可直接进入 `/t-task $ARGUMENTS`
- 如文档内容较多或结构复杂，可使用 `/t-html-show .ai/design/$ARGUMENTS.md` 生成 HTML 可视化预览

## 用户故事引用规则

正确：
- 引用故事 ID、标题、优先级、来源文件
- 总结场景名和核心约束

错误：
- 大段复制完整用户故事
- 粘贴完整 Gherkin
- 把用户故事改写成与原意冲突的需求

## 质量检查清单

生成前逐项自检：
- 是否遵循 `.ai/prd + docs/prd + .ai/user-stories + docs/user-stories 混合验证 / .ai/tech-research -> ${CLAUDE_PLUGIN_ROOT}/guides/ -> code` 的信息优先级
- 如果没有 PRD/用户故事，是否明确声明这是纯技术方案设计且不涉及业务逻辑变动
- 是否使用真实文件路径
- 是否避免过度设计
- 是否与现有代码架构一致
- 每个适用端是否都有分端文档，且由对应设计 agent 生成
- backend 分端设计是否满足 API、数据库、领域逻辑底线要求
- frontend/flutter 分端设计是否只消费契约、不重新定义契约
- frontend/flutter 分端设计的用户可见交互是否以用户体验描述为主，技术实现是否保持最小映射
- 主文档 §8 是否全量汇总各端文件影响范围且无遗漏
- 数据库设计是否遵循"尽量简洁，不默认展开审计"
- 是否包含测试策略和风险
- 是否仅把不需要用户选择的证据限制写入“已确认假设与证据限制”
- 是否 `needs_user_answer=0`
- 是否所有影响设计的 Active Decision 均在主文档 Decision Trace 中有 Applied / Not Applicable / Superseded 结论
- 是否通过 `check-decision-closure.py`（主文档与全部分端文档）

## 失败处理

- 参数缺失：终止并给出 `/t-design [方案名称]` 示例
- 文件名非法：终止并说明允许字符范围
- 无法创建输出目录或写文件：终止并报告
- 未找到足够需求文档：若影响设计判断，使用 `AskUserQuestion` 补齐并停止；不影响时只记录不需要用户选择的证据限制
- 子 agent 返回 `needs_user_answer`：按 Topic 查 Decision Log；未解决时提问并停止，回答后更新 Decision Log 并重新调度该端
- 子 agent 失败或超时：终止该端，不写入该端成功状态，报告失败 agent 与原因；其余端可继续
- 跨端契约冲突：以 backend 契约为准修正客户端分端设计；产品语义级冲突升级为 `AskUserQuestion`
- 决策闭合扫描失败：按 Decision Exposure Gate 分类；需要用户裁决时提问并停止，修正后重新扫描
- 代码分析失败：继续，但标记"现有实现分析不完整"
