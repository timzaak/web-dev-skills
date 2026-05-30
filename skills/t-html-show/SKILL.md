---
name: t-html-show
description: Generate HTML Preview for any Markdown document, helping humans quickly understand content.
argument-hint: "[feature-name | document-path]"
allowed-tools:
  - Read
  - Agent
  - Write
  - Bash
---

# 文档 HTML Preview 生成

运行时边界统一参考：`protocols/runtime-boundaries.md`

若本 skill、spec 或既有文档之间冲突，停止、说明冲突并等待澄清；不要平均折中。

## 适用范围

不要用它做：
- PRD 创建或更新 → 使用 `/t-prd`
- PRD 完整性检查 → 使用 `/t-prd-check`
- 修改源文档语义 → 先更新源文档，再重新生成 Preview

## 目标

基于任意 Markdown 文档生成或更新 HTML Preview，用于人类快速理解文档内容。

输出文件：
- PRD: `.ai/preview/<domain>/[feature].html`
- 其他: `.ai/preview/[stem].html`

## 使用方式

```bash
# PRD 模式（向后兼容）
/t-html-show [feature]

# 通用模式（任意 Markdown 文件）
/t-html-show <path-to-markdown>
```

## 参数要求

两种模式：
1. **PRD 模式**：参数是 feature 名称，自动搜索 `docs/prd/**/*.md`
2. **通用模式**：参数是文件路径，直接使用

文件名仅允许英文、数字、空格、下划线、连字符。拒绝 `..`。长度限制 1 到 50 字符。

如果参数不合法，立即终止并提示正确用法。

## 核心约束

**路径与域**：
- Preview 写入 `.ai/preview/` 下，不进入代码仓库
- PRD 来源路径为 `docs/prd/<domain>/[feature].md`，输出 `.ai/preview/<domain>/[feature].html`
- 其他文档：输出 `.ai/preview/<stem>.html`

**Preview 边界**：
- 是源文档的可视化审阅视图，不能引入源文档未声明的新需求或规则
- 有前端/交互入口时，UI 示意聚焦文档定义的目标体验和关键状态
- 使用单文件 HTML、内联 CSS 和少量原生 JS，不依赖外部构建工具或 CDN
- 技术栈无关，浏览器直接打开即可审阅

**更新行为**：
- 已有同名 Preview → 以当前源文档语义为基准更新
- Preview 与源文档不一致时，以源文档为准

## Input Contract

上游输入：
- 源 Markdown 文档（必须存在）
- `${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md` — HTML Preview 通用契约
- `${CLAUDE_PLUGIN_ROOT}/templates/preview-template.html` — HTML 模板

PRD 模式额外读取：
- `docs/prd/<domain>/[feature].md` — PRD 文档
- `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md` — PRD 专用契约

如果源文档不存在，立即终止并提示先创建文档。

## Output Contract

下游产出：

`.ai/preview/...html` — HTML Preview，包含：
- 元数据、来源文档路径和一句话目标
- 从文档提取的关键内容，按逻辑分组
- 前端功能目标体验的低保真交互示意，或后端场景的流程图/状态图/能力矩阵

## 工作流程

### 1. 校验参数

- 检查参数非空且符合规则
- 缺失参数：直接失败并提示用法
- 将 `$ARGUMENTS` 作为唯一入参来源

### 2. 定位文档

判断模式：
- 参数匹配已有文件路径 → 通用模式，直接使用
- 参数不匹配文件路径 → PRD 模式，搜索 `docs/prd/**/*.md` 找到目标 PRD
  - 未找到 → 终止并提示先执行 `/t-prd`
  - 确定目标域（`auth | billing | core | integration`）

### 3. 检查已有 Preview

检查输出路径是否已存在：
- 不存在 → create 路径
- 已存在 → update 路径

### 4. 生成 HTML Preview

通过 Agent tool 委派 `html-show` subagent 生成或更新 Preview。

委派 prompt 必须包含：
- 源文档路径
- （agent 自动推断输出路径、文档类型和模式）

示例委派 prompt：

```text
使用 html-show 生成 HTML Preview。
源文档: <doc-path>
```

subagent 的详细规则见 `agents/html-show.md` 和 `protocols/html-show-contract.md`。

### 5. 打开 Preview

生成完成后，运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/open-html-show.py <preview-path> --root .
```

### 6. 收尾

完成后明确说明：
- Preview 路径
- 文档类型（PRD / 通用）
- 本次走 create 还是 update
- 可视化类型（interactive-preview / backend-flow / state-diagram / capability-matrix / acceptance-matrix / document-reader）
- PRD 模式下一步：`/t-prd-check [feature]` 验证一致性

## 失败处理

- 缺失参数 → 直接失败并提示用法
- 源文档不存在 → 终止并提示先创建文档
- 文件无法写入 → 终止并报告
- HTML Preview 无法生成 → 终止并报告
- HTML Preview 无法打开 → 报告失败和文件路径，保留已生成文件

## 质量门禁

- Preview 内容边界以 `protocols/html-show-contract.md` 为准
- PRD 模式额外遵循 `protocols/prd-preview-contract.md`
- PRD 模式 Preview 生成后建议运行 `/t-prd-check [feature]` 验证一致性

## 附加资源

- HTML Preview 模板：`${CLAUDE_PLUGIN_ROOT}/templates/preview-template.html`
- HTML Preview 通用契约：`protocols/html-show-contract.md`
- HTML Preview PRD 契约：`protocols/prd-preview-contract.md`
- HTML Preview 打开脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/open-html-show.py`
- HTML Preview 检查脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/check-html-show.py`
- HTML Preview subagent：`agents/html-show.md`

## 相关引用

- `skills/t-prd/SKILL.md`
- `skills/t-prd-check/SKILL.md`
