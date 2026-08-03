---
name: t-prd
description: Create or update draft PRD and user stories for a feature.
argument-hint: "[feature-name]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
---

# PRD 草稿维护

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
跨阶段决策连续性和用户决策暴露统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`

若本 skill、spec 或既有文档之间冲突，停止、说明冲突并等待澄清；不要平均折中。

## 目标

基于 Decision Brief、现有 user story、正式 PRD、已有 PRD 草稿和用户补充信息，先补齐必要的 draft user story，再创建或更新一份 PRD 草稿，供人类快速审阅。`.ai/prd` 和 `.ai/user-stories` 是实现前和实现期间的临时候选需求工作区，不是长期权威源。

输出文件：
- `.ai/prd/<domain>/[feature].md`
- `.ai/user-stories/<domain>/[feature].md`（如需新增或补齐用户故事）
- `.ai/decision-log/[feature].md`（存在或产生决策、已解决问题、延期问题时创建或更新）


## 参数要求

- `[feature]` 必须是 feature 名称
- 文件名仅允许英文、数字、空格、下划线、连字符

## 核心约束
以多年产品经理的身份去编写用户故事和产品需求文档。

**路径与域**：
- PRD 草稿写入 `.ai/prd/<domain>/[feature].md`
- draft user story 写入 `.ai/user-stories/<domain>/[feature].md`
- `<domain>` 只能是 `auth`、`billing`、`core`、`integration`
- `/t-prd` 不写入 `docs/prd/`；若父目录缺失，仅在目标域已明确时创建 `.ai/prd/<domain>/`
- `/t-prd` 不写入 `docs/user-stories/`；若需新增或补齐用户故事，只写 `.ai/user-stories/<domain>/`
- `.ai/prd` 和 `.ai/user-stories` 不作为长期权威源；它们在设计、任务、实现和验收期间作为候选需求输入保留
- PRD、用户故事和技术预研的读取与写入边界统一参考 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`

**PRD 内容边界**：
- 聚焦产品边界与规则，不承载接口 schema、数据库建表或技术方案
- 可以写：接口能力范围、访问控制原则、租户/realm 边界、兼容性要求、前端页面入口、关键交互、状态反馈约束
- 禁止写：具体端点（`GET/POST /api/...`）、请求/响应参数表、HTTP 状态码列表、数据库表结构/迁移方案、Java/TypeScript 类型定义

**更新行为**：
- 已有同名草稿 → update 路径，以草稿为基底逐章更新
- 无草稿但有同名正式 PRD → draft-from-published 路径，以正式 PRD 为基线创建草稿，不覆盖正式 PRD
- 无草稿且无正式 PRD → create 路径，使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/template.md)
- 已有同名 draft user story 文件 → 追加到合适章节，不重建

**user story 引用**：
- PRD 只引用相关用户故事（ID、标题、优先级、来源文件），不复制完整验收文本
- 已发布 user story 足够覆盖时，PRD 可直接引用 `docs/user-stories/...`
- 缺少或需要补齐的本轮用户故事写入 `.ai/user-stories/<domain>/<feature>.md`
- draft user story 可以按角色分组组织在同一 feature 文件中；不得直接追加到 `docs/user-stories`

## 提问规则

- `$ARGUMENTS` 是 feature 名称；用户已在命令或当前对话中给出的信息不重复追问
- 先读取现有文档和代码上下文，不询问可直接查明的事实
- 提问前必须读取 `.ai/decision-log/$ARGUMENTS.md` 并按 Topic 检查已确认决策和已解决问题；不得重复询问
- 目标、范围边界、业务规则、成功标准、关键异常、角色价值、验收信号或风险接受无法从已确认来源裁决时，必须使用 `AskUserQuestion`
- 一次只问一个；每个问题给出推荐答案，用户可接受、修改或拒绝
- 用户回答后先更新 `.ai/decision-log/$ARGUMENTS.md`，再更新 PRD 或 draft user story
- PRD 只记录已确认决策；需要用户回答的问题不得写入 Markdown PRD、风险、假设或收尾清单后继续交付
- 确实不影响当前 PRD 的延期问题只能写入 Decision Log，必须指定 owner stage 和 `Must Resolve Before`，并在本轮收尾中明确告知用户
- 如果存在 `.ai/decision/[feature].md`，PRD 必须承接其中 Verdict、Scope Direction、D0/D1 决策和 Handoff；不得把 Open Questions 写成已确认决策
- 如果 Decision Brief 的 Verdict 是 `Needs Clarification`、`Park` 或 `Reject`，停止并提示先回到 `/t-decision [feature]`

## PRD 前置澄清门禁

`/t-prd` 在写入 PRD 草稿前必须完成轻量澄清门禁：先研究事实，再对真正阻塞 PRD 的判断点逐一追问，直到足以形成可审阅的产品语义。

运行时维护一个临时 `PRD Grill Snapshot`，不写入 PRD 正文：

```text
PRD Grill Snapshot
- Problem statement: [一句话说明要解决的问题或目标能力]
- Success criteria: [可验收的成功信号，至少 1 条]
- Facts: [来自现有文档、代码、tech research 或当前对话的事实]
- Confirmed decisions: [用户已确认的产品决策]
- Open questions: [仍阻塞 PRD 的判断题]
```

门禁规则：
- Discover first：先读取 `docs/user-stories/`、`.ai/user-stories/`、`docs/prd/`、`.ai/prd/`、`.ai/tech-research/`、产品 guide 和必要代码上下文；能查明的事实不得问用户。
- Define next：只追问判断题，包括目标、范围边界、非目标、成功标准、关键异常、优先级取舍、角色价值和验收信号。
- Depth-first：同一问题分支未澄清前，不同时抛出多个无关问题；每轮只问一个，并给出推荐答案。
- Concrete only：若用户回答仍是"更好"、"尽快"、"合理"等模糊表达，继续追问同一判断点，要求给出可判断的范围、指标、状态或验收信号。
- Stop early：当 Snapshot 已能支撑一份可审阅 PRD 草稿且 `needs_user_answer=0` 时停止追问；不影响当前 PRD 的延期问题按 Decision Log 契约登记和告知，不写入 PRD。
- Hard boundary：Snapshot 是运行时澄清工具，不是交付物；PRD 只能写入已确认决策和已确认成功标准，不能写入未确认假设。

通过门禁的最低条件：
- 能写出一句话 `Problem statement`
- 至少确认 1 条 `Success criteria`
- 已确认本次包含范围和至少 1 条明确 out of scope 或"暂无明确排除项"
- 没有会改变 PRD 主体方向的阻塞问题

## Input Contract

上游输入（可选，如果存在会提升质量）：
- `docs/user-stories/**/*.md` — 用户故事文档
- `.ai/user-stories/**/*.md` — draft 用户故事文档
- `docs/prd/00-index.md` — 正式 PRD 索引
- `.ai/decision/[feature].md` — 产品立项决策简报（必须检查；存在时必须读取，来自 `/t-decision`）
- `.ai/decision-log/[feature].md` — 跨阶段决策账本（存在时必须读取）
- `docs/prd/<domain>/[feature].md` — 已发布正式 PRD（可选，用作草稿基线）
- `.ai/prd/<domain>/[feature].md` — 已有 PRD 草稿（可选，用作更新基线）
- `.ai/tech-research/[feature].md` — 技术可行性研究报告（可选，来自 `/t-tech-research`）
- `${CLAUDE_PLUGIN_ROOT}/guides/product/index.md` — 产品规范入口
- `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` — 用户故事规范
- `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` — 需求来源正式/候选边界
- `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` — 决策账本、提问前查重和决策暴露门禁

如果上游输入缺失，先按 Decision Exposure Gate 分类：可查事实由 skill 调查；需要用户裁决的信息必须提问；只有不需要用户选择的证据限制可以写入文档。

## Output Contract

下游产出：

`.ai/prd/<domain>/[feature].md` — PRD 草稿，包含：
- 相关用户故事引用
- 范围界定、需求概述、业务规则与状态
- 功能需求与验收目标
- API 相关约束 / 前端交互约束（各标明适用或不适用）
- 已确认决策
- 带稳定 Decision ID 的决策追踪
- 参考资料

`.ai/user-stories/<domain>/[feature].md` — draft 用户故事，按需新增或补齐。`/t-prd` 不写入 `docs/user-stories`。

## 工作流程

### 1. 选择目标域

先读取：
- `docs/prd/00-index.md`
- `.ai/decision-log/$ARGUMENTS.md`（存在时必须先读取）
- `.ai/decision/$ARGUMENTS.md`（必须检查；存在时从中提取 Verdict、Scope Direction、D0/D1 决策、Open Questions 和 Handoff）
- `docs/user-stories/00-index.md`
- `.ai/tech-research/$ARGUMENTS.md`（如已存在，从中提取技术需求和影响分析）
- `.ai/prd/**/*.md` 和 `docs/prd/**/*.md` 中与 `$ARGUMENTS` 相关的少量候选文件

根据已发布/候选用户故事、草稿/正式 PRD 和需求语义推断目标域。无法推断时用 `AskUserQuestion` 询问一次。

### 2. 检查已有文件

检查 `.ai/prd/<domain>/[feature].md` 和 `docs/prd/<domain>/[feature].md`：
- 草稿不存在且正式 PRD 不存在 → create 路径
- 草稿不存在但正式 PRD 存在 → draft-from-published 路径
- 草稿已存在 → update 路径

### 3. 收集信息

如已存在 `.ai/decision-log/$ARGUMENTS.md`，先提取 Active Decisions、Resolved Questions、Deferred Questions 和 Superseded Decisions。到达本阶段最迟解决点的 Deferred Question 必须在写 PRD 前解决。

如已存在 `.ai/decision/$ARGUMENTS.md`，先从中提取目标用户、问题陈述、范围方向、已确认产品决策、仍阻塞 PRD 的问题和给 PRD 的 Handoff。若 Verdict 不允许继续进入 PRD，停止并提示回到 `/t-decision`。

若 Decision Brief、现有 PRD 或 Tech Research 含已确认决策但账本不存在或缺少对应记录，按 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` 初始化或补齐稳定 DEC ID；不得把 Open Questions、风险或假设升级成已确认决策。

如已存在 `.ai/tech-research/$ARGUMENTS.md`，再从中提取技术需求（§1.2）、代码库评估（§2）、影响分析（§5）和 PRD 建议（§7）。

仅当上下文无法可靠推断时，用 `AskUserQuestion` 补齐：
- 功能目标与范围边界
- 相关角色（优先使用仓库既有体系，如 Admin Realm、Regular User 等）
- 关键依赖或前置能力

以下信息优先从现有文档和代码推断，不作为默认提问项：
- 是否需要后端 API → 从技术研究报告或代码结构推断
- 是否需要前端实现 → 从技术研究报告或代码结构推断

如需新建 user story，额外确认：
- 目标用户价值
- 至少 1 个主验收场景
- 默认优先级（P0/P1/P2）

### 4. 执行 PRD 前置澄清门禁

基于已收集信息建立临时 `PRD Grill Snapshot`，并按"PRD 前置澄清门禁"检查是否满足最低条件。

不得：
- 把 Snapshot 原文写入 PRD
- 把未确认的 open question 写成 PRD 决策
- 为追求完整性持续追问非阻塞细节
- 询问仓库中可直接查明的事实

### 5. 检查、补齐并关联 user story

读取：
- `docs/user-stories/00-index.md`、`_README.md`、`_roles.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/product/index.md` 和 `user-story.md`
- 搜索 `docs/user-stories/**/*.md`、`.ai/user-stories/**/*.md`、`docs/prd/**/*.md` 和 `.ai/prd/**/*.md`

执行：
- 已存在足够覆盖的 user story → 直接引用，不重复创建
- 缺少少量场景 → 写入或追加 `.ai/user-stories/<domain>/<feature>.md`
- 已有同名 draft user story → 在其中追加合适章节，不重建
- 从已有草稿/正式 PRD 提取交叉引用和已有能力边界

新增 user story 必须遵循 `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` 的结构和 GWT 风格验收标准，使用 [user-story-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/user-story-template.md)。

补齐后仍不足时：
- 若缺口影响产品语义、范围、角色、业务状态或验收目标，使用 `AskUserQuestion` 并停止写入。
- 若产品语义已确认、仅缺独立 user story 文件，则把它作为追踪覆盖工作补齐，不得写成待用户确认。

### 6. 生成 PRD 草稿

create 路径使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/template.md)；draft-from-published 和 update 路径按核心约束中的"更新行为"逐章处理。

写入 `.ai/prd/<domain>/[feature].md`，至少包含：
- 相关用户故事、范围界定、需求概述、业务规则与状态
- 功能需求、验收目标
- API 相关约束 / 前端交互约束（各标明适用或不适用）
- 已确认决策及 Decision ID、参考资料

写入后运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py .ai/prd/<domain>/$ARGUMENTS.md
```

扫描命中时按 Decision Exposure Gate 分类并处理；重新扫描通过前不得交付 PRD。

不适用的章节保留并标记"不适用"。如需技术细节，建议执行 `/t-design`。

### 7. 人机迭代

如果用户基于 PRD 草稿提出修改意见：
- 表达方式调整 → 更新 Markdown PRD 草稿
- 产品语义调整 → 更新 Markdown PRD 草稿，并同步必要的 draft user story
- 与既有 Decision Brief、正式 PRD 或 user story 冲突时，以用户最新确认的意图为准；先创建新的 DEC 并设置 `Supersedes`，再在草稿中记录覆盖关系，不得复用旧 DEC ID 改写历史

### 8. 收尾

完成后明确说明：
- user story 文件路径和变更方式（新增/追加）
- 若本轮产生 draft user story，说明其为 `.ai/user-stories` 候选来源，需在 `/t-prd-publish` 阶段合并到 `docs/user-stories`
- PRD 草稿路径、所属域
- Decision Log 路径和本轮新增/复用/替代的 DEC/Q ID
- 本次走 create、draft-from-published 还是 update
- 验证风险或追踪覆盖工作；不得把需要用户回答的问题包装成后续提醒
- 延期问题：明确说明“无”，或列出已写入 Decision Log 且已指定 owner stage / Must Resolve Before 的 Q ID
- 下一步：若仍有会改变产品范围、业务规则、用户流程或验收目标的技术未知，先运行 `/t-tech-research [feature]`，再重跑 `/t-prd [feature]` 收敛草稿；否则高风险或复杂需求建议运行 `/t-prd-check [feature]`，简单需求可直接执行 `/t-design [feature]`

推断部分需在收尾对话中显式列出：哪些来自现有文档、哪些来自当前对话、哪些是 agent 有权作出的决定、哪些是无需用户选择的验证动作。完成交付时不得仍有 `needs_user_answer`。

## 失败处理

- 缺失 feature → 直接失败并提示参数
- 目标域无法判断 → 提示选择
- 文件无法写入 → 终止并报告
- user story 信息不足 → 先分类；影响产品语义时补问并停止，不影响产品语义时补齐追踪文件或记录验证动作
- 决策闭合扫描失败 → 按 Decision Exposure Gate 分类；需要用户裁决时提问并停止，修正后重新扫描
- Decision Brief 阻塞 PRD → 终止并提示 `/t-decision [feature]`

## 质量门禁

- 新增 PRD 草稿前应尽量具备可引用的 user story
- PRD 草稿内容边界以"核心约束"一节为准
- `needs_user_answer=0`，且决策闭合扫描通过
- 所有影响 PRD 的 Active Decision 均在“已确认决策”中按 Decision ID 追踪
- 进入 `/t-design` 前，PRD 草稿与已有技术预研不得存在未解释冲突
- 新草稿创建后建议按风险决定是否运行 `/t-prd-check [feature]`

## 附加资源

- PRD 模板：[template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/template.md)
- User Story 模板：[user-story-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/user-story-template.md)
