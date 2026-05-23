---
name: t-prd
description: Create or update PRD, HTML Preview, and user stories for a feature.
argument-hint: [feature-name]
allowed-tools:
  - AskUserQuestion
  - Read
  - Agent
  - Glob
  - Grep
  - Write
  - Bash
---

# PRD 维护

运行时边界统一参考：`protocols/runtime-boundaries.md`

若本 skill、spec 或既有文档之间冲突，停止、说明冲突并等待澄清；不要平均折中。

## 适用范围

这是一个有副作用的任务型 skill，负责先补齐 user story，再创建或更新 PRD 文档，并同步生成可视化 HTML Preview。

不要用它做：
- PRD 完整性检查 → 使用 `/t-prd-check`
- 用户故事质量检查 → 使用 `/t-prd-check`
- 实施进度或完成情况记录 → 使用对应实现阶段命令或任务状态文件，不写入 PRD

## 目标

基于现有 user story、PRD 索引、已有 PRD 和用户补充信息，先补齐必要的 user story，再创建或更新一份 PRD，并生成同目录 HTML Preview，供人类快速审阅和后续 `/t-design` 使用。

输出文件：
- `docs/prd/<domain>/[feature].md`
- `docs/prd/<domain>/[feature].html`

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

以下约束在本 skill 中为唯一权威来源，工作流步骤不再重复声明。

**路径与域**：
- PRD 写入 `docs/prd/<domain>/[feature].md`，HTML Preview 写入同目录 `[feature].html`
- `<domain>` 只能是 `auth`、`billing`、`core`、`integration`
- 不写入 `docs/prd/` 根目录；若父目录缺失，仅在目标域已明确时创建所需目录

**PRD 内容边界**：
- 聚焦产品边界与规则，不承载接口 schema、数据库建表或技术方案
- 可以写：接口能力范围、访问控制原则、租户/realm 边界、兼容性要求、前端页面入口、关键交互、状态反馈约束
- 禁止写：具体端点（`GET/POST /api/...`）、请求/响应参数表、HTTP 状态码列表、数据库表结构/迁移方案、Rust/TypeScript 类型定义
- 禁止写：当前任务是否已实现、完成比例、已完成/未完成清单等会随实现推进快速过期的进度状态

**HTML Preview 边界**：
- 是 Markdown PRD 的可视化审阅视图，不能引入 PRD 未声明的新需求或规则
- 有前端/交互入口时，UI 示意聚焦 PRD 定义的目标体验和关键状态，不复刻代码库已经具备的现有页面或组件；已有 UI 只作为入口或约束说明
- 使用单文件 HTML、内联 CSS 和少量原生 JS，不依赖外部构建工具或 CDN
- 技术栈无关，浏览器直接打开即可审阅

**更新行为**：
- 已有同名 PRD → update 路径，逐章比对本次确认信息：冲突章节替换冲突部分，一致章节保留，未涉及章节保留（代表之前决策），模板要求但缺失的章节补齐；已确认的"待确认假设"迁移至"已确认决策"
- 已有同名 user story 文件 → 追加到合适章节，不重建
- 已有同名 HTML Preview → 以当前 PRD 语义为基准更新

**user story 引用**：
- PRD 只引用相关用户故事（ID、标题、优先级、来源文件），不复制完整验收文本
- user story 优先追加到现有角色文件；只有现有分组明显不适合时才新增单独文件

## 提问规则

- `$ARGUMENTS` 是 Claude Code 传入的 feature 名称；用户已在命令或当前对话中给出的信息不重复追问
- 先读取现有文档和代码上下文，不询问可直接查明的事实
- 只在目标域、范围边界或补充 user story 所需信息无法可靠推断时，才使用 `AskUserQuestion`
- 一次只问一个；每个问题给出推荐答案，用户可接受、修改或拒绝
- 记录已确认决策和待确认假设，后续 PRD 与 HTML Preview 必须沿用
- 信息足够生成可审阅 PRD 时停止追问，不为了完美而继续打断

## 职责边界

- `/t-prd`：补齐 user story → 创建/更新 PRD → 生成 HTML Preview → 打开供人类审阅
- `/t-prd-check`：检查 PRD、HTML Preview 与用户故事质量（不在本 skill 范围内）
- `/t-design`：基于 PRD 生成技术设计（不在本 skill 范围内）
- 本 skill 产出产品语义文档，不负责接口明细、数据库设计或技术实现方案

## Input Contract

上游输入（可选，如果存在会提升质量）：
- `docs/user-stories/**/*.md` — 用户故事文档
- `docs/prd/00-index.md` — PRD 索引
- `${CLAUDE_PLUGIN_ROOT}/guides/product/index.md` — 产品规范入口
- `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` — 用户故事规范
- `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md` — HTML Preview 产物契约
- `.ai/tech-research/[feature].md` — 技术可行性研究报告（可选，来自 `/t-tech-research`）

如果上游输入缺失，skill 仍可运行，但会在文档中标记缺失项。

## Output Contract

下游产出（供 `/t-prd-check` 和 `/t-design` 使用）：

`docs/prd/<domain>/[feature].md` — PRD 文档，包含：
- 相关用户故事引用
- 范围界定、需求概述、业务规则与状态
- 功能需求与验收目标
- API 相关约束 / 前端交互约束（各标明适用或不适用）
- 已确认决策与待确认假设
- 参考资料

`docs/prd/<domain>/[feature].html` — HTML Preview，包含：
- 元数据、来源路径和一句话目标
- 目标能力、范围、流程、业务状态、规则、验收目标和待确认假设
- 前端功能目标体验的低保真交互示意，或后端场景的流程图/状态图/能力矩阵

可能更新用户故事文件（追加或新建）。

## 工作流程

### 1. 校验参数

- 检查 `[feature]` 非空且符合文件名规则
- 缺失 feature：直接失败并提示参数
- 将 `$ARGUMENTS` 作为 feature 名称唯一入参来源

### 2. 选择目标域

先读取：
- `docs/prd/00-index.md`
- `docs/user-stories/00-index.md`
- `.ai/tech-research/$ARGUMENTS.md`（如已存在，从中提取技术需求和影响分析）

根据用户故事和需求语义推断目标域（`auth | billing | core | integration`）。无法推断时用 `AskUserQuestion` 询问一次。

### 3. 检查已有文件

检查 `docs/prd/<domain>/[feature].md` 和 `.html`：
- 不存在 → create 路径
- 已存在 → update 路径

### 4. 收集信息

如已存在 `.ai/tech-research/$ARGUMENTS.md`，先从中提取技术需求（§1.2）、代码库评估（§2）、影响分析（§5）和 PRD 建议（§7），减少提问量。

仅当上下文无法可靠推断时，用 `AskUserQuestion` 补齐：
1. 功能目标与范围边界
2. 相关角色（优先使用仓库既有体系，如 Admin Realm、Regular User 等）
3. 关键依赖或前置能力

以下信息优先从现有文档和代码推断，不作为默认提问项：
- 是否需要后端 API → 从技术研究报告或代码结构推断
- 是否需要前端实现 → 从技术研究报告或代码结构推断

如需新建 user story，额外确认：
4. 目标用户价值
5. 至少 1 个主验收场景
6. 默认优先级（P0/P1/P2）

### 5. 检查、补齐并关联 user story

读取：
- `docs/user-stories/00-index.md`、`_README.md`、`_roles.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/product/index.md` 和 `user-story.md`
- 搜索 `docs/user-stories/**/*.md` 和 `docs/prd/**/*.md`

执行：
- 已存在足够覆盖的 user story → 直接引用，不重复创建
- 缺少少量场景 → 优先在对应角色现有文件中追加
- 现有角色文件都不适合 → 创建新文件
- 从已有 PRD 提取交叉引用和已有能力边界，避免重复定义

新增 user story 必须遵循 `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` 的结构和 GWT 风格验收标准，使用 [user-story-template.md](user-story-template.md)。

补齐后仍不够 → 继续生成 PRD，在文档中标记"待补充用户故事"。

### 6. 生成 PRD

create 路径使用 [template.md](template.md)；update 路径以现有 PRD 为基底，按核心约束中的"更新行为"逐章处理。

写入 `docs/prd/<domain>/[feature].md`，至少包含：
- 相关用户故事、范围界定、需求概述、业务规则与状态
- 功能需求、验收目标
- API 相关约束 / 前端交互约束（各标明适用或不适用）
- 已确认决策与待确认假设、参考资料

不适用的章节保留并标记"不适用"。如需技术细节，建议执行 `/t-design`。

### 7. 生成 HTML Preview

通过 Agent tool 委派 `prd-preview` subagent 生成或更新 `docs/prd/<domain>/[feature].html`。

委派 prompt 必须包含：
- PRD 路径和 Preview 输出路径
- 本次是 create 还是 update
- 用户当前确认的目标、范围、流程、业务状态、规则、验收目标和待确认假设

示例委派 prompt：

```text
使用 prd-preview 生成 PRD HTML Preview。
PRD: docs/prd/<domain>/[feature].md
Preview: docs/prd/<domain>/[feature].html
Mode: create|update
要求：遵循 protocols/prd-preview-contract.md；如为纯后端场景，使用流程图/状态图/能力矩阵，不生成伪 UI。
前端 UI 示意只展示 PRD 定义的目标体验，不复刻已有实现。
```

subagent 的详细规则见 `agents/prd-preview.md` 和 `protocols/prd-preview-contract.md`。

生成完成后，运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/open-html-preview.py docs/prd/<domain>/[feature].html --root .
```

### 8. 人机迭代

如果用户基于 HTML Preview 提出修改意见：
- 表达方式调整 → 只更新 HTML
- 产品语义调整 → 先更新 Markdown PRD，再同步 HTML
- 两者不一致时，以用户最新确认的意图为准

### 9. 收尾

完成后明确说明：
- user story 文件路径和变更方式（新增/追加）
- PRD 和 HTML Preview 路径、所属域
- 本次走 create 还是 update
- 需要重点补充或确认的部分
- 下一步：`/t-prd-check [feature]` 或 `/t-design [feature]`

推断部分需显式列出：哪些来自现有文档、哪些来自当前对话、哪些仍是待确认假设。

## 失败处理

- 缺失 feature → 直接失败并提示参数
- 目标域无法判断 → 提示选择 `auth|billing|core|integration`
- 文件无法写入 → 终止并报告
- user story 信息不足 → 先补问；仍不足则继续，PRD 中标记缺口
- HTML Preview 无法生成 → 终止并报告，不能只交付 Markdown PRD
- HTML Preview 无法打开 → 报告失败和文件路径，保留已生成文件

## 质量门禁

- 新增 PRD 前应尽量具备可引用的 user story
- PRD 和 HTML Preview 内容边界以"核心约束"一节为准
- HTML Preview 必须存在并符合 `protocols/prd-preview-contract.md`
- 新文档创建后建议立即运行 `/t-prd-check [feature]`

## 附加资源

- PRD 模板：[template.md](template.md)
- User Story 模板：[user-story-template.md](user-story-template.md)
- HTML Preview 模板：[preview-template.html](preview-template.html)
- HTML Preview 契约：`protocols/prd-preview-contract.md`
- HTML Preview 打开脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/open-html-preview.py`
- HTML Preview subagent：`agents/prd-preview.md`

## 相关引用

- `skills/t-prd-check/SKILL.md`
- `skills/t-design/SKILL.md`
