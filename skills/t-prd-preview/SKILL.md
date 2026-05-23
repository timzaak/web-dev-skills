---
name: t-prd-preview
description: Generate HTML Preview for PRD visual review.
argument-hint: [feature-name]
allowed-tools:
  - Read
  - Agent
  - Write
  - Bash
---

# PRD HTML Preview 生成

运行时边界统一参考：`protocols/runtime-boundaries.md`

若本 skill、spec 或既有文档之间冲突，停止、说明冲突并等待澄清；不要平均折中。

## 适用范围

这是一个有副作用的任务型 skill，负责将 Markdown PRD 转化为可视化 HTML Preview，供人类快速审阅和协作。

不要用它做：
- PRD 创建或更新 → 使用 `/t-prd`
- PRD 完整性检查 → 使用 `/t-prd-check`
- 修改 PRD 产品语义 → 先用 `/t-prd` 更新 PRD，再重新生成 Preview

## 目标

基于 Markdown PRD 生成或更新同 feature 的 HTML Preview，用于人类快速理解、反馈和修改功能目标、用户路径、状态变化和待确认假设。

输出文件：
- `.ai/preview/<domain>/[feature].html`

## 使用方式
```bash
/t-prd-preview [feature]
```

## 参数要求

- `[feature]` 必须是 feature 名称
- 文件名仅允许英文、数字、空格、下划线、连字符
- 拒绝 `..`, `/`, `\`
- 长度限制 1 到 50 字符

如果参数不合法，立即终止并提示正确用法。

## 核心约束

**路径与域**：
- Preview 写入 `.ai/preview/<domain>/[feature].html`，不进入代码仓库
- `<domain>` 只能是 `auth`、`billing`、`core`、`integration`
- PRD 来源路径为 `docs/prd/<domain>/[feature].md`

**Preview 边界**：
- 是 Markdown PRD 的可视化审阅视图，不能引入 PRD 未声明的新需求或规则
- 有前端/交互入口时，UI 示意聚焦 PRD 定义的目标体验和关键状态，不复刻代码库已经具备的现有页面或组件；已有 UI 只作为入口或约束说明
- 使用单文件 HTML、内联 CSS 和少量原生 JS，不依赖外部构建工具或 CDN
- 技术栈无关，浏览器直接打开即可审阅

**更新行为**：
- 已有同名 Preview → 以当前 PRD 语义为基准更新
- Preview 与 PRD 不一致时，以 PRD 为准

## Input Contract

上游输入（来自 `/t-prd` 产出）：
- `docs/prd/<domain>/[feature].md` — PRD 文档（必须存在）
- `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md` — HTML Preview 产物契约
- `${CLAUDE_PLUGIN_ROOT}/skills/t-prd-preview/preview-template.html` — HTML 模板

如果 PRD 不存在，立即终止并提示先执行 `/t-prd`。

## Output Contract

下游产出（供 `/t-prd-check` 使用）：

`.ai/preview/<domain>/[feature].html` — HTML Preview，包含：
- 元数据、来源 PRD 路径和一句话目标
- 目标能力、范围、流程、业务状态、规则、验收目标和待确认假设
- 前端功能目标体验的低保真交互示意，或后端场景的流程图/状态图/能力矩阵

## 工作流程

### 1. 校验参数

- 检查 `[feature]` 非空且符合文件名规则
- 缺失 feature：直接失败并提示参数
- 将 `$ARGUMENTS` 作为 feature 名称唯一入参来源

### 2. 定位 PRD

- 搜索 `docs/prd/**/*.md` 找到目标 PRD
- 未找到 → 终止并提示先执行 `/t-prd`
- 确定目标域（`auth | billing | core | integration`）

### 3. 检查已有 Preview

检查 `.ai/preview/<domain>/[feature].html`：
- 不存在 → create 路径
- 已存在 → update 路径

### 4. 生成 HTML Preview

通过 Agent tool 委派 `prd-preview` subagent 生成或更新 `.ai/preview/<domain>/[feature].html`。

委派 prompt 必须包含：
- PRD 路径和 Preview 输出路径
- 本次是 create 还是 update
- 用户当前确认的目标、范围、流程、业务状态、规则、验收目标和待确认假设

示例委派 prompt：

```text
使用 prd-preview 生成 PRD HTML Preview。
PRD: docs/prd/<domain>/[feature].md
Preview: .ai/preview/<domain>/[feature].html
Mode: create|update
要求：遵循 protocols/prd-preview-contract.md；如为纯后端场景，使用流程图/状态图/能力矩阵，不生成伪 UI。
前端 UI 示意只展示 PRD 定义的目标体验，不复刻已有实现。
```

subagent 的详细规则见 `agents/prd-preview.md` 和 `protocols/prd-preview-contract.md`。

### 5. 打开 Preview

生成完成后，运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/open-html-preview.py .ai/preview/<domain>/[feature].html --root .
```

### 6. 收尾

完成后明确说明：
- Preview 路径和所属域
- 本次走 create 还是 update
- 可视化类型（interactive-preview / backend-flow / state-diagram / capability-matrix / acceptance-matrix）
- 下一步：`/t-prd-check [feature]` 验证一致性

## 失败处理

- 缺失 feature → 直接失败并提示参数
- PRD 不存在 → 终止并提示先执行 `/t-prd`
- 文件无法写入 → 终止并报告
- HTML Preview 无法生成 → 终止并报告
- HTML Preview 无法打开 → 报告失败和文件路径，保留已生成文件

## 质量门禁

- Preview 内容边界以 `protocols/prd-preview-contract.md` 为准
- Preview 生成后建议运行 `/t-prd-check [feature]` 验证一致性

## 附加资源

- HTML Preview 模板：[preview-template.html](preview-template.html)
- HTML Preview 契约：`protocols/prd-preview-contract.md`
- HTML Preview 打开脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/open-html-preview.py`
- HTML Preview subagent：`agents/prd-preview.md`

## 相关引用

- `skills/t-prd/SKILL.md`
- `skills/t-prd-check/SKILL.md`
