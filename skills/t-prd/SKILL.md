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

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（判断产物写入位置或项目事实与插件默认冲突时读）
决策连续性和用户决策暴露：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`（提问、更新决策账本或处理决策暴露门禁时读）

若本 skill、spec 或既有文档之间冲突，停止、说明冲突并等待澄清；不要平均折中。

## 目标

基于 Decision Brief、现有 user story、正式 PRD、已有 PRD 草稿和用户补充信息，先补齐必要的 draft user story，再创建或更新一份 PRD 草稿，供人类快速审阅。`.ai/prd` 和 `.ai/user-stories` 是实现前和实现期间的临时候选需求工作区，不是长期权威源。

输出文件：
- `.ai/prd/<domain>/[feature].md` — PRD 草稿，至少包含：相关用户故事引用、范围界定、需求概述、业务规则与状态、功能需求与验收目标、API 相关约束 / 前端交互约束（各标明适用或不适用）、已确认决策及 Decision ID、参考资料
- `.ai/user-stories/<domain>/[feature].md` — draft user story，按需新增或补齐
- `.ai/decision-log/[feature].md` — 存在，或产生用户决策、问题状态变化或重要 AI 决策时创建或更新

## 参数要求

- `[feature]` 必须是 feature 名称；文件名仅允许英文、数字、空格、下划线、连字符
- 缺失或非法时终止并提示参数格式

## 核心约束

**路径与域**：
- `<domain>` 只能是 `auth`、`billing`、`core`、`integration`；父目录缺失且目标域已明确时才创建对应 `.ai/` 子目录
- `/t-prd` 不写入 `docs/prd/` 和 `docs/user-stories/`
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
- 缺少或需要补齐的本轮用户故事写入 `.ai/user-stories/<domain>/<feature>.md`；draft user story 可以按角色分组组织在同一 feature 文件中

## 提问与澄清门禁

写入 PRD 草稿前必须完成轻量澄清门禁。运行时维护临时 `PRD Grill Snapshot`（澄清工具，不是交付物，不写入 PRD 正文）：

```text
PRD Grill Snapshot
- Problem statement: [一句话说明要解决的问题或目标能力]
- Success criteria: [可验收的成功信号，至少 1 条]
- Facts: [来自现有文档、代码、tech research 或当前对话的事实]
- Confirmed decisions: [用户已确认的产品决策]
- Open questions: [仍阻塞 PRD 的判断题]
```

提问纪律：

- **Discover first**：先读现有文档、代码、tech research 和产品 guide；能查明的事实不问用户，用户已给信息不重复追问。提问前按 Topic 检查 `.ai/decision-log/$ARGUMENTS.md`，已确认的不重复问。
- **只问判断题**：目标、范围边界、非目标、成功标准、关键异常、优先级取舍、角色价值、验收信号或风险接受无法从已确认来源裁决时，必须使用 `AskUserQuestion`；不得把这类问题写入 PRD、风险、假设或收尾清单后继续交付。
- **Depth-first**：一次只问一个，给出推荐答案（用户可接受、修改或拒绝）；回答仍是"更好""尽快""合理"等模糊表达时继续追问，要求可判断的范围、指标、状态或验收信号。
- **回答入账**：用户回答后先更新 `.ai/decision-log/$ARGUMENTS.md`，再更新 PRD 或 draft user story。
- **Stop early**：Snapshot 能支撑可审阅草稿且 `needs_user_answer=0` 时停止追问；不影响当前 PRD 的延期问题按 Decision Log 契约登记（owner stage + `Must Resolve Before`）并在收尾告知用户，不写入 PRD。

门禁最低通过条件：能写出一句话 `Problem statement`；至少确认 1 条 `Success criteria`；已确认本次包含范围和至少 1 条明确 out of scope（或"暂无明确排除项"）；没有会改变 PRD 主体方向的阻塞问题。

## Input Contract

上游输入（可选，存在时提升质量；先索引、后明细，`.ai/decision-log` 和 `.ai/decision` 必须最先检查）：
- `.ai/decision/[feature].md` — 产品立项决策简报（必须检查；存在时必须读取，来自 `/t-decision`）
- `.ai/decision-log/[feature].md` — 跨阶段决策账本（存在时必须读取）
- `docs/user-stories/**/*.md` — 用户故事文档
- `.ai/user-stories/**/*.md` — draft 用户故事文档
- `docs/prd/00-index.md` — 正式 PRD 索引
- `docs/prd/<domain>/[feature].md` — 已发布正式 PRD（可选，用作草稿基线）
- `.ai/prd/<domain>/[feature].md` — 已有 PRD 草稿（可选，用作更新基线）
- `.ai/tech-research/[feature].md` — 技术可行性研究报告（可选，来自 `/t-tech-research`）
- `${CLAUDE_PLUGIN_ROOT}/guides/product/index.md` — 产品规范入口
- `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` — 用户故事规范

上游输入缺失时按 Decision Exposure Gate 分类：可查事实由 skill 调查；需要用户裁决的信息必须提问；只有不需要用户选择的证据限制可以写入文档。

## 工作流程

### 1. 选择目标域并检查已有文件

按 Input Contract 读取上游输入，根据已发布/候选用户故事、草稿/正式 PRD 和需求语义推断目标域；无法推断时用 `AskUserQuestion` 询问一次。检查 `.ai/prd/<domain>/[feature].md` 和 `docs/prd/<domain>/[feature].md`，按"更新行为"选择 create / draft-from-published / update 路径。

### 2. 收集信息

- 从 `.ai/decision-log/$ARGUMENTS.md` 提取 Active Decisions、Resolved Questions、Deferred Questions 和 Superseded Decisions；到达本阶段最迟解决点的 Deferred Question 必须在写 PRD 前解决。
- 从 `.ai/decision/$ARGUMENTS.md` 提取目标用户、问题陈述、范围方向、已确认产品决策、阻塞问题和给 PRD 的 Handoff。Verdict 为 `Needs Clarification`、`Park` 或 `Reject` 时停止并提示回到 `/t-decision`。若 Brief、现有 PRD 或 Tech Research 含已确认决策但账本缺少对应记录，按 decision-continuity-contract 初始化或补齐稳定 DEC ID；不得把 Open Questions、风险或假设升级成已确认决策。
- 如已存在 `.ai/tech-research/$ARGUMENTS.md`，从中提取技术需求（§1.2）、代码库评估（§2）、影响分析（§5）和 PRD 建议（§7）。
- 仅当上下文无法可靠推断时，用 `AskUserQuestion` 补齐：功能目标与范围边界、相关角色（优先使用仓库既有体系）、关键依赖或前置能力。是否需要后端 API / 前端实现优先从技术预研或代码结构推断，不作为默认提问项。
- 如需新建 user story，额外确认：目标用户价值、至少 1 个主验收场景、默认优先级（P0/P1/P2）。

### 3. 执行澄清门禁

基于已收集信息建立 `PRD Grill Snapshot`，按"提问与澄清门禁"推进到达标。

### 4. 检查、补齐并关联 user story

读取 `docs/user-stories/00-index.md`、`_README.md`、`_roles.md`、`${CLAUDE_PLUGIN_ROOT}/guides/product/index.md` 和 `user-story.md`，并搜索 `docs/user-stories/**/*.md`、`.ai/user-stories/**/*.md`、`docs/prd/**/*.md` 和 `.ai/prd/**/*.md`。

执行：
- 已存在足够覆盖的 user story → 直接引用，不重复创建
- 缺少少量场景 → 写入或追加 `.ai/user-stories/<domain>/<feature>.md`
- 从已有草稿/正式 PRD 提取交叉引用和已有能力边界

新增 user story 必须遵循 `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` 的结构和 GWT 风格验收标准，使用 [user-story-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/user-story-template.md)。

补齐后仍不足时：缺口影响产品语义、范围、角色、业务状态或验收目标 → 按提问纪律补问并停止写入；产品语义已确认、仅缺独立 user story 文件 → 作为追踪覆盖工作补齐，不得写成待用户确认。

### 5. 生成 PRD 草稿

create 路径使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/template.md)；draft-from-published 和 update 路径按"更新行为"逐章处理。不适用章节保留并标记"不适用"。写入后运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py .ai/prd/<domain>/$ARGUMENTS.md
```

命中项按 Decision Exposure Gate 分类处理；重新扫描通过前不得交付 PRD。如需技术细节，建议执行 `/t-design`。

### 6. 人机迭代

用户基于 PRD 草稿提出修改意见时：
- 表达方式调整 → 更新 Markdown PRD 草稿
- 产品语义调整 → 更新 PRD 草稿，并同步必要的 draft user story
- 与既有 Decision Brief、正式 PRD 或 user story 冲突 → 以用户最新确认意图为准；先创建新 DEC 并设置 `Supersedes`，再在草稿中记录覆盖关系，不得复用旧 DEC ID 改写历史

### 7. 收尾

完成后明确说明：
- user story 文件路径和变更方式（新增/追加）；若本轮产生 draft user story，说明其为 `.ai/user-stories` 候选来源，需在 `/t-prd-publish` 阶段合并到 `docs/user-stories`
- PRD 草稿路径、所属域、本轮路径类型（create / draft-from-published / update）
- Decision Log 路径和本轮新增/复用/替代的 DEC/Q ID
- 验证风险或追踪覆盖工作；延期问题明确说明"无"或列出已登记的 Q ID
- 推断部分显式列出来源（现有文档 / 当前对话 / agent 自主决定 / 验证动作）
- 下一步：仍有会改变产品范围、业务规则、用户流程或验收目标的技术未知时，先运行 `/t-tech-research [feature]` 再重跑 `/t-prd` 收敛；否则高风险或复杂需求建议 `/t-prd-check [feature]`，简单需求可直接 `/t-design [feature]`

## 失败处理

- 缺失 feature 或文件无法写入：终止并报告
- Decision Brief 阻塞 PRD：终止并提示 `/t-decision [feature]`
- user story 信息不足：影响产品语义时按提问纪律补问并停止；不影响时补齐追踪文件或记录验证动作

## 质量门禁

- 新增 PRD 草稿前应尽量具备可引用的 user story
- `needs_user_answer=0`，且决策闭合扫描通过
- 所有影响 PRD 的 Active Decision 均在"已确认决策"中按 Decision ID 追踪
- 进入 `/t-design` 前，PRD 草稿与已有技术预研不得存在未解释冲突

## 附加资源

- PRD 模板：[template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/template.md)
- User Story 模板：[user-story-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/user-story-template.md)
