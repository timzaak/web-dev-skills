---
name: t-prd
description: Create or update draft PRD, HTML Preview, and user stories for a feature.
argument-hint: "[feature-name]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Agent
  - Glob
  - Grep
  - Write
  - Bash
---

# PRD 草稿维护

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

若本 skill、spec 或既有文档之间冲突，停止、说明冲突并等待澄清；不要平均折中。

## 适用范围

不要用它做：
- PRD 完整性检查 → 使用 `/t-prd-check`
- 用户故事质量检查 → 使用 `/t-prd-check`
- 实施进度或完成情况记录 → 使用对应实现阶段命令或任务状态文件，不写入 PRD

## 目标

基于 Decision Brief、现有 user story、正式 PRD、已有 PRD 草稿和用户补充信息，先补齐必要的 user story，再创建或更新一份 PRD 草稿，并生成 HTML Preview，供人类快速审阅。`.ai/prd` 是实现前和实现期间的临时候选需求工作区，不是长期权威源。

输出文件：
- `.ai/prd/<domain>/[feature].md`

## 使用方式

```bash
/t-prd [feature]
```

## 参数要求

- `[feature]` 必须是 feature 名称
- 文件名仅允许英文、数字、空格、下划线、连字符
- 拒绝 `..`, `/`, `\`
- 长度限制 1 到 50 字符

如果参数不合法，立即终止并提示正确用法。

## 核心约束

**路径与域**：
- PRD 草稿写入 `.ai/prd/<domain>/[feature].md`
- HTML Preview 由 `/t-html-show` 写入 `.ai/preview/<domain>/[feature].html`
- `<domain>` 只能是 `auth`、`billing`、`core`、`integration`
- `/t-prd` 不写入 `docs/prd/`；若父目录缺失，仅在目标域已明确时创建 `.ai/prd/<domain>/`
- `.ai/prd` 不作为长期权威源；它在设计、任务、实现和验收期间作为候选需求输入保留

**PRD 内容边界**：
- 聚焦产品边界与规则，不承载接口 schema、数据库建表或技术方案
- 可以写：接口能力范围、访问控制原则、租户/realm 边界、兼容性要求、前端页面入口、关键交互、状态反馈约束
- 禁止写：具体端点（`GET/POST /api/...`）、请求/响应参数表、HTTP 状态码列表、数据库表结构/迁移方案、Rust/TypeScript 类型定义
- 禁止写：当前任务是否已实现、完成比例、已完成/未完成清单等会随实现推进快速过期的进度状态

**更新行为**：
- 已有同名草稿 → update 路径，以草稿为基底逐章更新
- 无草稿但有同名正式 PRD → draft-from-published 路径，以正式 PRD 为基线创建草稿，不覆盖正式 PRD
- 无草稿且无正式 PRD → create 路径，使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/template.md)
- 已有同名 user story 文件 → 追加到合适章节，不重建
- 已有同名 HTML Preview → 以当前草稿 PRD 语义为基准更新

**user story 引用**：
- PRD 只引用相关用户故事（ID、标题、优先级、来源文件），不复制完整验收文本
- user story 优先追加到现有角色文件；只有现有分组明显不适合时才新增单独文件

## 提问规则

- `$ARGUMENTS` 是 Claude Code 传入的 feature 名称；用户已在命令或当前对话中给出的信息不重复追问
- 先读取现有文档和代码上下文，不询问可直接查明的事实
- 只在目标域、范围边界、成功标准或补充 user story 所需信息无法可靠推断时，才使用 `AskUserQuestion`
- 一次只问一个；每个问题给出推荐答案，用户可接受、修改或拒绝
- PRD 只记录已确认决策；仍待确认的信息在对话收尾中列出，不写入 Markdown PRD
- 如果存在 `.ai/decision/[feature].md`，PRD 必须承接其中 Verdict、Scope Direction、D0/D1 决策和 Handoff；不得把 Open Questions 写成已确认决策
- 如果 Decision Brief 的 Verdict 是 `Needs Clarification`、`Park` 或 `Reject`，停止并提示先回到 `/t-decision [feature]`
- 信息足够生成可审阅 PRD 草稿时停止追问，不为了完美而继续打断

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
- Discover first：先读取 `docs/user-stories/`、`docs/prd/`、`.ai/prd/`、`.ai/tech-research/`、产品 guide 和必要代码上下文；能查明的事实不得问用户。
- Define next：只追问判断题，包括目标、范围边界、非目标、成功标准、关键异常、优先级取舍、角色价值和验收信号。
- Depth-first：同一问题分支未澄清前，不同时抛出多个无关问题；每轮只问一个，并给出推荐答案。
- Concrete only：若用户回答仍是"更好"、"尽快"、"合理"等模糊表达，继续追问同一判断点，要求给出可判断的范围、指标、状态或验收信号。
- Stop early：当 Snapshot 已能支撑一份可审阅 PRD 草稿时停止追问；其余非阻塞疑问作为待确认项在收尾对话列出。
- Hard boundary：Snapshot 是运行时澄清工具，不是交付物；PRD 只能写入已确认决策和已确认成功标准，不能写入未确认假设。

通过门禁的最低条件：
- 能写出一句话 `Problem statement`
- 至少确认 1 条 `Success criteria`
- 已确认本次包含范围和至少 1 条明确 out of scope 或"暂无明确排除项"
- 没有会改变 PRD 主体方向的阻塞问题

## 职责边界

- `/t-prd`：补齐 user story → 创建/更新 `.ai/prd` 草稿 → 触发 `/t-html-show` 生成 HTML Preview
- `/t-html-show`：基于 PRD 草稿生成 HTML Preview（通过本 skill 自动触发）
- `/t-prd-check`：检查 PRD 草稿、HTML Preview、正式 PRD 基线和用户故事质量（不在本 skill 范围内）
- `/t-design`：基于通过检查的草稿 PRD 与正式 PRD 的混合验证生成技术设计（不在本 skill 范围内）
- 本 skill 产出产品语义草稿，不负责接口明细、数据库设计或技术实现方案

## Input Contract

上游输入（可选，如果存在会提升质量）：
- `docs/user-stories/**/*.md` — 用户故事文档
- `docs/prd/00-index.md` — 正式 PRD 索引
- `.ai/decision/[feature].md` — 产品立项决策简报（推荐，来自 `/t-decision`）
- `docs/prd/<domain>/[feature].md` — 已发布正式 PRD（可选，用作草稿基线）
- `.ai/prd/<domain>/[feature].md` — 已有 PRD 草稿（可选，用作更新基线）
- `.ai/tech-research/[feature].md` — 技术可行性研究报告（可选，来自 `/t-tech-research`）
- `${CLAUDE_PLUGIN_ROOT}/guides/product/index.md` — 产品规范入口
- `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` — 用户故事规范
- `${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md` — HTML Preview 通用契约
- `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md` — HTML Preview PRD 专用契约

如果上游输入缺失，skill 仍可运行，但会在文档中标记缺失项。

## Output Contract

下游产出（供 `/t-prd-check` 和 `/t-design` 使用）：

`.ai/prd/<domain>/[feature].md` — PRD 草稿，包含：
- 相关用户故事引用
- 范围界定、需求概述、业务规则与状态
- 功能需求与验收目标
- API 相关约束 / 前端交互约束（各标明适用或不适用）
- 已确认决策
- 参考资料

可能更新用户故事文件（追加或新建）。

HTML Preview 由 `/t-html-show` 自动生成到 `.ai/preview/<domain>/[feature].html`，不进入代码仓库。

## 工作流程

### 1. 校验参数

- 检查 `[feature]` 非空且符合文件名规则
- 缺失 feature：直接失败并提示参数
- 将 `$ARGUMENTS` 作为 feature 名称唯一入参来源

### 2. 选择目标域

先读取：
- `docs/prd/00-index.md`
- `.ai/decision/$ARGUMENTS.md`（如存在，从中提取 Verdict、Scope Direction、D0/D1 决策、Open Questions 和 Handoff）
- `docs/user-stories/00-index.md`
- `.ai/tech-research/$ARGUMENTS.md`（如已存在，从中提取技术需求和影响分析）
- `.ai/prd/**/*.md` 和 `docs/prd/**/*.md` 中与 `$ARGUMENTS` 相关的少量候选文件

根据用户故事、草稿/正式 PRD 和需求语义推断目标域（`auth | billing | core | integration`）。无法推断时用 `AskUserQuestion` 询问一次。

### 3. 检查已有文件

检查 `.ai/prd/<domain>/[feature].md` 和 `docs/prd/<domain>/[feature].md`：
- 草稿不存在且正式 PRD 不存在 → create 路径
- 草稿不存在但正式 PRD 存在 → draft-from-published 路径
- 草稿已存在 → update 路径

### 4. 收集信息

如已存在 `.ai/decision/$ARGUMENTS.md`，先从中提取目标用户、问题陈述、范围方向、已确认产品决策、仍阻塞 PRD 的问题和给 PRD 的 Handoff。若 Verdict 不允许继续进入 PRD，停止并提示回到 `/t-decision`。

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

### 5. 执行 PRD 前置澄清门禁

基于已收集信息建立临时 `PRD Grill Snapshot`，并按"PRD 前置澄清门禁"检查是否满足最低条件。

不得：
- 把 Snapshot 原文写入 PRD
- 把未确认的 open question 写成 PRD 决策
- 为追求完整性持续追问非阻塞细节
- 询问仓库中可直接查明的事实

### 6. 检查、补齐并关联 user story

读取：
- `docs/user-stories/00-index.md`、`_README.md`、`_roles.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/product/index.md` 和 `user-story.md`
- 搜索 `docs/user-stories/**/*.md`、`docs/prd/**/*.md` 和 `.ai/prd/**/*.md`

执行：
- 已存在足够覆盖的 user story → 直接引用，不重复创建
- 缺少少量场景 → 优先在对应角色现有文件中追加
- 现有角色文件都不适合 → 创建新文件
- 从已有草稿/正式 PRD 提取交叉引用和已有能力边界

新增 user story 必须遵循 `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` 的结构和 GWT 风格验收标准，使用 [user-story-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/user-story-template.md)。

补齐后仍不够 → 继续生成 PRD 草稿，在文档中标记"待补充用户故事"。

### 7. 生成 PRD 草稿

create 路径使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/template.md)；draft-from-published 和 update 路径按核心约束中的"更新行为"逐章处理。

写入 `.ai/prd/<domain>/[feature].md`，至少包含：
- 相关用户故事、范围界定、需求概述、业务规则与状态
- 功能需求、验收目标
- API 相关约束 / 前端交互约束（各标明适用或不适用）
- 已确认决策、参考资料

不适用的章节保留并标记"不适用"。如需技术细节，建议执行 `/t-design`。

### 8. 生成 HTML Preview

通过 Agent tool 委派 `html-show` subagent 自动生成或更新 HTML Preview。

委派 prompt 包含：
- 源文档路径（agent 自动推断输出路径、类型和模式）

示例委派 prompt：

```text
使用 html-show 生成 HTML Preview。
源文档: .ai/prd/<domain>/[feature].md
```

`html-show` subagent 会基于指定草稿生成 `.ai/preview/<domain>/[feature].html`。生成完成后用系统默认浏览器打开该 HTML 文件。

如果 html-show 失败，终止并报告，不能只交付 Markdown PRD 草稿。

### 9. 人机迭代

如果用户基于 HTML Preview 提出修改意见：
- 表达方式调整 → 只更新 HTML
- 产品语义调整 → 先更新 Markdown PRD 草稿，再同步 HTML
- 两者不一致时，以用户最新确认的意图为准

### 10. 收尾

完成后明确说明：
- user story 文件路径和变更方式（新增/追加）
- PRD 草稿路径、所属域
- HTML Preview 路径（`.ai/preview/<domain>/[feature].html`）
- 本次走 create、draft-from-published 还是 update
- 需要重点补充或确认的部分
- 待确认项：明确说明"无"或以对话形式列出，不写入 Markdown PRD
- 下一步：`/t-prd-check [feature]`；通过后执行 `/t-design [feature]`，若检查发现问题则修复后再次运行 `/t-prd-check [feature]`

推断部分需在收尾对话中显式列出：哪些来自现有文档、哪些来自当前对话、哪些仍待确认；未确认内容不写入 Markdown PRD。

## 失败处理

- 缺失 feature → 直接失败并提示参数
- 目标域无法判断 → 提示选择 `auth|billing|core|integration`
- 文件无法写入 → 终止并报告
- user story 信息不足 → 先补问；仍不足则继续，PRD 中标记缺口
- HTML Preview 无法生成 → 终止并报告，不能只交付 Markdown PRD
- Decision Brief 阻塞 PRD → 终止并提示 `/t-decision [feature]`
- HTML Preview 无法打开 → 报告失败和文件路径（`.ai/preview/<domain>/[feature].html`），保留已生成文件

## 质量门禁

- 新增 PRD 草稿前应尽量具备可引用的 user story
- PRD 草稿和 HTML Preview 内容边界以"核心约束"一节为准
- HTML Preview 必须存在并符合 `${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md` 和 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md`
- 新草稿创建后建议立即运行 `/t-prd-check [feature]`

## 附加资源

- PRD 模板：[template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/template.md)
- User Story 模板：[user-story-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-prd/user-story-template.md)
