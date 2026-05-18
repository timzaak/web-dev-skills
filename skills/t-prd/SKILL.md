---
name: t-prd
description: Create or update PRD, HTML Preview, and user stories for a feature.
argument-hint: [feature-name]
allowed-tools:
  - AskUserQuestion
  - Read
  - Task
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
- 实施状态更新 → 使用对应实现阶段命令

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

- PRD 必须写入 `docs/prd/<domain>/[feature].md`
- HTML Preview 必须写入 `docs/prd/<domain>/[feature].html`
- `<domain>` 只能是现有一级目录：`auth`、`billing`、`core`、`integration`
- 不写入 `docs/prd/` 根目录
- user story 优先追加到现有角色文件；只有现有分组明显不适合时才新增单独文件
- PRD 只引用相关用户故事，不复制完整验收文本
- PRD 聚焦产品边界与规则，不承载接口 schema、数据库建表或技术方案
- HTML Preview 是 Markdown PRD 的可视化审阅视图，不能引入 PRD 未声明的新需求或规则
- HTML Preview 必须目标技术栈无关，使用单文件 HTML、内联 CSS 和少量原生 JS
- 如果已有同名 PRD，默认进入 update 路径，而不是覆盖重写

## Claude Code 参数与提问规则

- `$ARGUMENTS` 是 Claude Code 传入的 feature 名称；如果用户已经在命令或当前对话中给出完整信息，不要重复追问
- 只有在目标域、范围边界或补充 user story 所需信息无法从现有文档和当前对话可靠推断时，才使用 `AskUserQuestion`
- 提问应限于补齐最小必要缺口，不重复询问已明确给出的功能目标、角色或约束
- 写文件前先确认目标路径位于 `docs/prd/<domain>/` 或 `docs/user-stories/` 下；若父目录缺失，仅在目标域已明确时创建所需目录
- 若目标 PRD 已存在，默认执行 update，不整篇覆盖；若目标 user story 文件已存在，默认追加到合适章节，而不是重建文件
- 若同名 HTML Preview 已存在，默认以当前 PRD 语义为基准更新，不保留与 PRD 冲突的旧交互或旧规则

## 职责边界

- `/t-prd` 负责先补齐相关 user story，再创建或更新 PRD
- `/t-prd` 必须同步生成同目录 HTML Preview
- `/t-prd` 生成或更新 HTML Preview 后必须立即打开该 HTML，进入人类审阅和迭代
- `/t-prd-check` 负责检查 PRD 与用户故事质量
- `/t-prd-check` 负责检查 HTML Preview 的存在性、可审阅性和 PRD 一致性
- `/t-prd` 不负责 `check`
- `/t-prd` 产出产品语义文档，不负责生成接口明细、数据库设计或技术实现方案

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
- `docs/prd/<domain>/[feature].md` — PRD 文档，包含：
  - 相关用户故事引用（ID、标题、优先级、来源文件）
  - 范围界定（包含/不包含）
  - 需求概述
  - 功能需求与验收目标
  - API 相关约束（如适用）
  - 前端/交互约束（如适用）
  - 相关文件索引
- `docs/prd/<domain>/[feature].html` — PRD HTML Preview，包含：
  - PRD 元数据、来源路径和一句话目标
  - 用户故事、范围、流程、状态、规则、验收目标和待确认假设
  - 前端功能的低保真交互示意，或后端复杂场景的流程图/状态图/能力矩阵
- 可能更新的用户故事文件（追加或新建）

## 工作流程

### 1. 校验参数

- 检查 `[feature]` 非空且符合文件名规则
- 缺失 feature：直接失败并提示参数
- 将 `$ARGUMENTS` 作为 feature 名称唯一入参来源；若仅有自然语言需求而无 feature 名称，先要求用户明确名称

### 2. 选择目标域

先读取：
- `docs/prd/00-index.md`
- `docs/user-stories/00-index.md`
- `.ai/tech-research/$ARGUMENTS.md`（如已存在，从中提取技术需求、依赖信息和影响分析）

然后确定目标域：
- `auth`
- `billing`
- `core`
- `integration`

优先根据用户故事和需求语义推断。
如果无法可靠推断，再用 `AskUserQuestion` 询问一次目标域。

### 3. 检查是否已存在

检查目标文件：
- `docs/prd/<domain>/[feature].md`
- `docs/prd/<domain>/[feature].html`

判定规则：
- 文件不存在：进入 create 路径
- 文件已存在：进入 update 路径

update 路径要求：
- 保留已有有效章节和稳定语义
- 只补齐缺失内容、修正冲突、整理结构失衡部分
- 不因局部缺口整篇重写 PRD

### 4. 收集最小必要信息

如果已存在 `.ai/tech-research/$ARGUMENTS.md`，从中提取以下信息以减少重复提问：
- 技术需求提取（报告第 1.2 节）
- 现有代码库评估结果（报告第 2 节）
- 影响分析（报告第 5 节）
- PRD 编写建议（报告第 7 节）

如果当前上下文仍不够，使用 `AskUserQuestion` 只补齐这些信息：
1. 功能目标
2. 相关角色
3. 范围边界
4. 是否需要后端 API
5. 是否需要前端实现
6. 关键依赖或前置能力

其中：
- "是否需要后端 API" 只用于判断是否写入 API 能力边界、权限原则和接口约束，不展开端点清单
- "是否需要前端实现" 只用于判断是否写入页面入口、关键交互和状态反馈约束，不展开组件实现方案
- 已在当前对话或现有文档中明确的信息不得再次提问

角色名称应优先使用仓库既有体系，例如：
- `Admin Realm`
- `Realm Admin`
- `Regular User`
- `Third-Party App`
- `TOTP User`
- `Billing User`
- `Points Admin`
- `Points User`

如果需要新建或补充 user story，还必须拿到：
7. 目标用户价值
8. 至少 1 个主验收场景
9. 默认优先级（P0/P1/P2）

需求收敛规则：
- 先读取现有文档和代码上下文，不询问可直接查明的事实。
- 只问会影响产品判断的问题；一次只问一个。
- 每个问题给出推荐答案，用户可接受、修改或拒绝。
- 记录已确认决策和待确认假设，后续 PRD 与 HTML Preview 必须沿用。
- 信息足够生成可审阅 PRD 时停止追问，不为了完美而继续打断。

### 5. 检查并补齐 user story

先读取：
- `docs/user-stories/00-index.md`
- `docs/user-stories/_README.md`
- `docs/user-stories/_roles.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/product/index.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md`

然后搜索真实目录：
- `docs/user-stories/**/*.md`

执行规则：
- 如果已存在足够覆盖该功能的 user story，直接引用，不重复创建
- 如果只缺少少量场景，优先在对应角色现有文件中追加故事
- 如果现有角色文件都不适合，才创建新的 user story 文件

优先复用现有角色文件，例如：
- `01-admin-realm-user-stories.md`
- `02-realm-admin-user-stories.md`
- `03-regular-user-user-stories.md`
- `04-third-party-app-user-stories.md`
- 以及仓库内已有的专项 story 文件

新增或补充 user story 时必须遵循：
- 使用 `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` 的结构和约束
- 引用 `docs/user-stories/_roles.md`
- 聚焦用户行为和价值，不写 API、数据表、实现细节
- 使用 GWT 风格验收标准

如需新增/补充，使用 [user-story-template.md](user-story-template.md) 作为结构模板。

### 6. 关联用户故事与现有文档

搜索真实目录：
- `docs/user-stories/**/*.md`
- `docs/prd/**/*.md`

优先从索引定位，再读取相关明细。

至少提取：
- 用户故事 ID、标题、优先级、来源文件
- 相关业务规则或现有 PRD 交叉引用
- 已有能力边界，避免重复定义

如果补齐后仍没有足够用户故事：
- 继续生成 PRD
- 在文档中显式标记"待补充用户故事"

### 7. 生成 PRD

create 路径使用 [template.md](template.md) 作为模板初始化；update 路径以现有 PRD 为基底增补和整理，写入：
- `docs/prd/<domain>/[feature].md`

文档至少包含：
- 相关用户故事
- 范围界定
- 需求概述
- 当前实现状态
- 功能需求
- API 相关约束（如适用）
- 前端/交互约束（如适用）
- 已确认决策与待确认假设
- 相关文件索引
- 参考资料

不适用的章节保留并标记"不适用"。

生成 PRD 时必须遵循：
- 可以写接口能力范围、访问控制原则、租户/realm 边界、兼容性要求、相关接口说明位置
- 可以写前端页面入口、关键交互、可见性、反馈约束
- 禁止写具体端点、请求参数表、响应字段表、HTTP 状态码列表
- 禁止写数据库表结构、迁移方案、DDL、Rust/TypeScript 类型定义
- 需要技术细节时，引用或建议补充 `/t-design` 产出的技术设计文档

### 8. 生成 HTML Preview

通过 `prd-preview` subagent 生成或更新：
- `docs/prd/<domain>/[feature].html`

委派 prompt 必须包含：
- PRD 路径：`docs/prd/<domain>/[feature].md`
- Preview 输出路径：`docs/prd/<domain>/[feature].html`
- 相关用户故事路径和摘要
- 本次是 create 还是 update
- 用户当前确认的目标、范围、流程、状态、规则、验收目标和待确认假设

示例：

```text
使用 prd-preview 生成 PRD HTML Preview。
PRD: docs/prd/<domain>/[feature].md
Preview: docs/prd/<domain>/[feature].html
Mode: create|update
Related stories: <paths and IDs>
要求：遵循 protocols/prd-preview-contract.md；如为纯后端场景，使用流程图/状态图/能力矩阵，不生成伪 UI。
```

`prd-preview` subagent 负责具体可视化表达、后端流程图选择、HTML 结构和机械检查。详细规则只看：
- `agents/prd-preview.md`
- `protocols/prd-preview-contract.md`

生成或更新完成后，必须立即运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/open-html-preview.py docs/prd/<domain>/[feature].html --root .
```

如果用户基于 HTML Preview 提出修改意见，必须同步更新：
- `docs/prd/<domain>/[feature].html`
- `docs/prd/<domain>/[feature].md`

人机迭代规则：
- 表达方式调整：只更新 HTML。
- 产品语义调整：先更新 Markdown PRD，再同步 HTML。
- 两者不一致时，以用户最新确认的意图为准修正。

### 9. 收尾输出

完成后明确说明：
- user story 文件路径和变更方式（新增/追加）
- 文档路径
- HTML Preview 路径
- 所属域
- 本次执行走的是 create 还是 update 路径
- 需要重点补充或确认的部分
- 下一步：`/t-prd-check [feature]`
- 如需进入设计：`/t-design [feature]`

如果因信息不完整而做了推断，需显式列出：
- 哪些内容来自现有文档
- 哪些内容来自当前对话
- 哪些内容仍是待用户确认的假设

## 失败处理

- 缺失 feature：直接失败并提示参数。
- 目标域无法判断且用户未提供：提示选择 `auth|billing|core|integration`。
- 文件无法写入：终止并报告。
- user story 信息不足：先补问；仍不足则继续，但在 PRD 中写出缺口。
- HTML Preview 无法生成：终止并报告，不能只交付 Markdown PRD。
- HTML Preview 无法打开：报告打开失败和文件路径，但仍保留已生成文件，等待用户手动打开或继续指示。

## 质量门禁

- 新增 PRD 前应尽量具备可引用的 user story；缺失时先补齐。
- PRD 至少包含：相关用户故事、范围界定、需求概述、当前实现状态、功能需求、API 相关约束（如适用）、前端/交互约束（如适用）、已确认决策与待确认假设、相关文件索引、参考资料。
- PRD 禁止写入：`GET/POST /api/...` 端点清单、请求/响应 schema、HTTP 状态码矩阵、数据库建表/迁移细节、Rust/TypeScript 数据结构示例。
- HTML Preview 必须存在并符合 `protocols/prd-preview-contract.md`。
- 新文档创建后建议立即运行 `/t-prd-check [feature]`。

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
