---
name: t-html-show
description: Generate HTML Preview for any Markdown document, helping humans quickly understand content.
argument-hint: "[document-path]"
allowed-tools:
  - Read
  - Agent
  - Write
  - Bash
---

# 文档 HTML Preview 生成

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

若本 skill、spec 或既有文档之间冲突，停止、说明冲突并等待澄清；不要平均折中。

## 适用范围

不要用它做：
- PRD 创建或更新 → 使用 `/t-prd`
- PRD 完整性检查 → 使用 `/t-prd-check`
- 修改源文档语义 → 先更新源文档，再重新生成 Preview

## 目标

基于任意 Markdown 文档生成或更新 HTML Preview。

参数是源 Markdown 文档路径。文档类型由路径自动推断，输出路径按类型派生：

- PRD: `.ai/prd/<domain>/<feature>.md` 或 `docs/prd/<domain>/<feature>.md` → `.ai/preview/<domain>/<feature>.html`
- Decision Brief: `.ai/decision/<feature>.md` → `.ai/preview/decision/<feature>.html`
- Tech Research: `.ai/tech-research/<feature>.md` → `.ai/preview/tech-research/<feature>.html`
- Design: `.ai/design/<feature>.md` → `.ai/preview/design/<feature>.html`
- Task: `.ai/task/<feature>/.../<name>.md` → `.ai/preview/task/<feature>/.../<name>.html`
- 其他: `<path>/<name>.md` → `.ai/preview/<name>.html`

## 使用方式

```bash
/t-html-show <path-to-markdown>
```

## 参数要求

参数必须是源 Markdown 文档的文件路径，直接使用。拒绝 `..`。

如果参数不合法，立即终止并提示正确用法。

## 核心约束

**路径与域**：
- Preview 写入 `.ai/preview/` 下，不进入代码仓库
- 文档类型与输出路径由源文档路径派生，规则见上方「目标」

**Preview 边界**：
- 是源文档的可视化审阅视图，不能引入源文档未声明的新需求或规则
- 模板是解释型组件库；生成时必须按文档类型选择信息架构和主视觉，不为套模板编造内容
- 首屏必须突出结论、主视觉和注意项，不得把 Markdown 章节流水账搬进 HTML
- 主视觉必须是 graph/matrix/timeline/swimlane/pipeline/hub map/inline SVG/interactive preview 等关系表达
- `insight`、`signal`、普通段落和 `.card` 不算主视觉；连续 3 个以上 card 视为不合格
- 有前端/交互入口时，UI 示意聚焦文档定义的目标体验和关键状态
- 允许使用外部脚本、样式、CDN、npm 包、构建工具、第三方图库或辅助资源；如使用，必须在 Preview 可见区域声明依赖来源、用途和打开/运行方式
- 辅助资源必须写入 `.ai/preview/` 下与主 HTML 同名或同目录的资源目录，不得写入目标项目源码

**更新行为**：
- 已有同名 Preview → 以当前源文档语义为基准更新
- Preview 与源文档不一致时，以源文档为准

## Input Contract

上游输入：
- 源 Markdown 文档（必须存在）
- `${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md` — HTML Preview 通用契约
- `${CLAUDE_PLUGIN_ROOT}/templates/preview-template.html` — HTML 模板

当源文档为 PRD（路径位于 `.ai/prd/**` 或 `docs/prd/**`）时额外读取：
- `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md` — PRD 专用契约

如果源文档不存在，立即终止并提示先创建文档。

## Output Contract

下游产出：

`.ai/preview/...html` — HTML Preview，包含：
- 元数据、来源文档路径和一句话目标
- 从文档提取的 3-5 个关键事实（受工作记忆 4±1 chunks 约束），按人类审阅任务重组
- 一个主视觉区域和注意项区域，用于快速传达重点、变化、依赖、风险或下一步
- 前端功能目标体验的低保真交互示意，或后端场景的流程图、状态图、依赖图、时间线、泳道图、能力矩阵、验收矩阵、风险热力、pipeline 或 hub map
- 外部依赖声明与打开/运行方式（如使用外部脚本、样式、CDN、npm 包、构建工具、第三方图库或辅助资源）

## 工作流程

### 1. 校验参数

- 检查参数非空且符合规则
- 缺失参数：直接失败并提示用法
- 将 `$ARGUMENTS` 作为唯一入参来源

### 2. 定位文档

- 参数即为源 Markdown 文档路径，直接使用
- 文档不存在 → 终止并提示先创建文档

### 3. 检查已有 Preview

检查输出路径是否已存在：
- 不存在 → create 路径
- 已存在 → update 路径

### 4. 生成 HTML Preview

按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 委派 `html-show` subagent 生成或更新 Preview。

委派 prompt 必须包含：
- 源文档路径
- （agent 自动推断输出路径、文档类型和模式）

示例委派 prompt：

```text
使用 html-show 生成 HTML Preview。
源文档: <doc-path>
```

subagent 的详细规则见 `${CLAUDE_PLUGIN_ROOT}/agents/html-show.md` 和 `${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md`。

### 5. 打开 Preview（可选，默认不打开）

生成完成后，默认不自动打开；只报告 `<preview-path>`（例如 `.ai/preview/<domain>/[feature].html`）和当前平台的打开命令。如 Preview 使用外部依赖、构建工具或本地服务，还必须报告可复现的安装/构建/启动命令。仅当用户在对话中明确要求打开时才执行，使用 `html-show-contract.md` 的 `Opening the Preview` 中定义的命令或 Preview 声明的运行命令并校验启动结果，不得谎报"已打开"。

### 6. 收尾

完成后明确说明：
- Preview 路径
- 文档类型（PRD / Decision / Tech Research / Design / Task / Generic）
- 本次走 create 还是 update
- 可视化类型（prd-review / decision-map / research-map / design-change-map / task-execution-map / answer-board / interactive-preview / backend-flow / state-diagram / dependency-graph / timeline / swimlane / pipeline / hub-map / capability-matrix / acceptance-matrix / document-reader）

## 失败处理

- 缺失参数或参数不是文件路径 → 直接失败并提示用法
- 源文档不存在 → 终止并提示先创建文档
- 文件无法写入 → 终止并报告
- HTML Preview 无法生成 → 终止并报告
- HTML Preview 无法打开 → 报告失败和文件路径，保留已生成文件

## 质量门禁

- Preview 内容边界以 `${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md` 为准
- PRD 文档额外遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md`

## 附加资源

- HTML Preview 模板：`${CLAUDE_PLUGIN_ROOT}/templates/preview-template.html`
- HTML Preview 通用契约：`${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md`
- HTML Preview PRD 契约：`${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md`
- HTML Preview 检查脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/check-html-show.py`
- HTML Preview subagent：`${CLAUDE_PLUGIN_ROOT}/agents/html-show.md`
