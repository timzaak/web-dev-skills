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
  - Write
  - Bash
---

# 技术设计文档生成

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
需求来源边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`
跨阶段决策连续性和用户决策暴露统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`

设计生成应保持简单、当前必需、可追溯；如果需求、spec、代码或本 skill 冲突，停止并说明冲突。

需要用户裁决的设计缺口必须通过 `AskUserQuestion` 解决，不得只写入风险、待确认事项或假设后继续生成。

## 适用范围

仅在以下场景使用：
- 用户明确要求"技术设计""方案设计""架构设计""API 设计""数据模型设计"
- 用户明确执行 `/t-design [方案名称]`
- 已经确认这是新功能或较大能力扩展，需要正式设计文档进入 DDD 流程

不要因为用户只是问"怎么实现""大概怎么做"就自动触发本 skill。

默认不用于以下前缀任务，除非用户明确要求补设计文档：
- `bugfix-`
- `refactor-`
- `doc-`
- `test-`
- `style-`

## 目标

基于用户故事、PRD 草稿、已发布 PRD 基线、技术预研、用户已准备的仓库内资料和现有代码，生成一份可实施、可追踪、可用于 `/t-task` 的技术设计文档。`/t-prd-check` 是推荐的可选上游检查；未运行时，本 skill 必须自行完成关键需求来源混合验证。

输出文件：
- `.ai/design/$ARGUMENTS.md`
- `.ai/decision-log/$ARGUMENTS.md`（复用上游决策并记录本阶段新 D2 决策或已解决问题）

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
- `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md` — 质量规范
- `AGENTS.md` — Agent 规范

## Output Contract

下游产出：
- `.ai/design/$ARGUMENTS.md` — 技术设计文档，包含：
  - 目标与范围
  - 用户故事/PRD/技术预研引用
  - 现有实现分析
  - 方案设计与关键取舍
  - API 接口设计（如适用）
  - 数据库设计（如适用）
  - 前端设计（如适用）
  - 测试策略
  - 风险与验证动作
  - 文件影响范围

推荐文档大小：300-500 行。超过 800 行应考虑拆分方案。

## 核心约束

- 业务功能设计必须混合验证 `.ai/prd` 草稿与 `docs/prd` 正式 PRD：草稿是当前候选需求，正式 PRD 是已发布基线；两者存在未说明冲突时停止并要求修正草稿，必要时运行 `/t-prd-check [feature]`
- 业务功能设计必须混合验证 `.ai/user-stories` draft 与 `docs/user-stories` 已发布故事：draft story 是当前候选需求，正式 story 是已发布基线；两者存在未说明冲突时停止并要求修正草稿，必要时运行 `/t-prd-check [feature]`
- 若存在 `.ai/decision/<feature>.md`，设计必须尊重其中目标用户、Scope Direction、D0/D1 产品决策和 Handoff；不得用技术方案静默改变立项结论
- 若存在 `.ai/decision-log/<feature>.md`，必须逐项承接影响设计的 Active Decision；不得重复询问 Resolved Question，也不得使用 Superseded Decision
- 若存在 `.ai/prd` 草稿且内容会影响设计，默认基于草稿继续设计，并在设计文档中标记是否已找到对应 PRD Check 报告；不得要求先发布到 `docs/prd`
- 若存在 `.ai/user-stories` draft 且内容会影响设计，默认基于 draft story 继续设计，并在设计文档中保留 `.ai/user-stories/...` 来源路径；不得要求先发布到 `docs/user-stories`
- 若没有 `.ai/prd` 草稿但存在 `docs/prd` 正式 PRD，可基于正式 PRD 继续设计，并在设计文档中标记"未发现 PRD 草稿"
- 纯技术方案没有 PRD/用户故事时，以 `.ai/tech-research/<feature>.md` 中的技术目标、约束和影响范围为准；执行流程与质量门禁以 `${CLAUDE_PLUGIN_ROOT}/guides/` 为准
- 没有 PRD/用户故事时，必须在设计文档中声明"纯技术方案设计，不涉及业务逻辑变动"，并引用对应 `.ai/tech-research/<feature>.md`
- 先读索引，再读相关明细
- 只引用用户故事，不粘贴完整故事正文或整段 Gherkin
- 优先复用现有实现，不凭空设计新架构
- 默认不搜索额外资料；人类在进入 `/t-design` 前应已准备好相关资料
- 只有在人类明确要求补充外部依据时，才可将外部资料作为附加参考
- 设计文档必须包含：目标、范围、API 接口设计、数据库设计、测试策略、风险
- 涉及前端时，必须包含页面/组件说明和页面线框说明
- 设计文档整体可保留 API 接口设计章节，但前端设计部分不单列 API 契约描述
- 数据库设计遵循"尽量简洁、当前必需、避免过度审计设计"
- 文档中的文件路径必须使用仓库真实路径，不允许使用不存在的示例路径

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
- `AGENTS.md`

## 工作流程

### 1. 验证参数和输出位置

- 校验 `$ARGUMENTS` 非空
- 文件名仅允许中文、英文、数字、空格、下划线、连字符
- 拒绝 `..`, `/`, `\`
- 长度限制 1 到 50 字符
- 确保 `.ai/design/` 目录存在
- 确保 `.ai/decision-log/` 存在

如果 `.ai/design/$ARGUMENTS.md` 已存在，先询问是否覆盖。

### 2. 收集最小必要输入

如果当前上下文里还没有足够信息，使用 `AskUserQuestion` 只补齐以下内容：
- 功能目标或问题陈述
- 人类已准备好的相关资料路径或名称
- 需要覆盖的范围边界

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

分析真实代码结构，不要假设 `backend/src` 存在。重点检查：
- `backend/api/`
- `backend/core/`
- `backend/sdk/`
- `backend/integration-tests/`
- `frontend/src/`
- `frontend/tests/`
- `demo/e2e/`（如需求涉及主故事验收）

需要输出：
- 现有实现入口
- 可复用模块
- 需要修改的边界
- 与当前架构或约束冲突的点

如果代码分析较复杂，使用 `Task` 启动 Explore agent，给出清晰任务：
- 找出现有实现位置
- 标出可复用点
- 标出最可能受影响的模块
- 返回具体文件路径和理由

### 5. 生成设计文档

使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-design/template.md) 作为结构模板生成 `.ai/design/$ARGUMENTS.md`。

输出内容必须满足：
- 有明确目标和范围
- 有用户故事（`.ai/user-stories` 或 `docs/user-stories`）/PRD 草稿/正式 PRD 引用；纯技术方案可改为技术预研引用，并声明不涉及业务逻辑变动
- 有现有实现分析
- 有方案设计与替代方案或关键取舍
- 有 API 接口设计、数据库设计、前端设计中的适用部分
- 有测试策略
- 有风险与验证动作；不得包含需要用户回答的问题
- 有 Decision Trace，逐项说明影响设计的 Active Decision 如何应用
- 有文件影响范围

如果某章节不适用，保留章节并标记"不适用"及原因。

写入后运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py .ai/design/$ARGUMENTS.md
```

扫描命中时按 Decision Exposure Gate 分类并处理；重新扫描通过前不得交付设计或建议进入 `/t-task`。

### 6. API 接口设计要求

适用时必须至少包含：
- 接口清单：方法、路径、用途、权限、调用方
- 关键接口的请求字段、响应字段、错误响应或状态码
- 路径参数占位符使用 camelCase，例如 `{realmId}`、`{userId}`
- 说明新增 DTO、复用 DTO、与现有 OpenAPI/SDK 的关系

禁止：
- 只给示例 JSON，不说明字段含义
- 只写"复用现有接口"但不指出具体路径或边界
- 使用与仓库规范冲突的 snake_case 路径参数

### 7. 数据库设计要求

适用时必须至少包含：
- 表或字段变更清单，达到可建表/可迁移粒度
- 每张表的主键、唯一约束、必要索引、外键、时间字段
- 字段类型或等价约束说明，避免"仅有字段名"
- 迁移策略摘要：新增表、加字段、改名、是否需要回填、兼容性影响

默认标准：
- 结构尽量简洁，只覆盖当前功能必需字段
- 优先最小必要约束与索引，不做过度索引
- 审计类表、通用审计字段、复杂审计方案默认不展开；只有需求明确要求时才补充
- 设计文档承接数据库结构与迁移影响，但不维护第二套手工运维流程

### 8. 前端设计要求

涉及前端时必须至少包含：
- 页面/路由/组件清单
- 页面线框说明：页面区域、主要交互、关键状态、数据来源或依赖
- 与现有前端模式的一致性说明，例如表单、查询、错误处理、路由承接方式
- `data-testid` 或 Demo 选择器影响（如涉及 Demo/E2E 验收）

注意：
- 整体设计文档中的 API 接口设计章节仍用于描述后端接口与 OpenAPI/SDK 关系
- 前端设计部分不再单独展开 API 契约，只保留实现所需的最小依赖说明

如果不涉及前端，显式写"不适用"与原因。

### 9. 收尾输出

完成后在响应中明确说明：
- 文档路径
- Decision Log 路径和本轮新增/复用/替代的 DEC/Q ID
- 本次设计覆盖的核心范围
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
- 是否与现有 Rust + React 架构一致
- 是否说明权限、错误处理、迁移/兼容性影响
- 是否补齐 API 接口设计、数据库设计与前端设计的适用内容
- 前端设计是否避免单列 API 契约描述，而是聚焦页面、交互、状态与依赖
- 数据库设计是否遵循"尽量简洁，不默认展开审计"
- 是否包含测试策略和风险
- 是否仅把不需要用户选择的证据限制写入“已确认假设与证据限制”
- 是否 `needs_user_answer=0`
- 是否所有影响设计的 Active Decision 均在 Decision Trace 中有 Applied / Not Applicable / Superseded 结论
- 是否通过 `check-decision-closure.py`

## 失败处理

- 参数缺失：终止并给出 `/t-design [方案名称]` 示例
- 文件名非法：终止并说明允许字符范围
- 无法创建输出目录或写文件：终止并报告
- 未找到足够需求文档：若影响设计判断，使用 `AskUserQuestion` 补齐并停止；不影响时只记录不需要用户选择的证据限制
- 决策闭合扫描失败：按 Decision Exposure Gate 分类；需要用户裁决时提问并停止，修正后重新扫描
- 代码分析失败：继续，但标记"现有实现分析不完整"

## 附加资源

- 设计文档结构模板：[template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-design/template.md)
- 决策连续性协议：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`
