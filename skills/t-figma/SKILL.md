---
name: t-figma
description: Restore a Figma design into an existing frontend file and verify fidelity via getComputedStyle measurement. Stack-agnostic (React/Vue/Svelte/Liquid/plain HTML/PHP...). Use when the user provides a Figma link and a target source file.
argument-hint: "<figma-url> <target-file>"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Agent
  - Write
  - Bash
  - mcp__figma__get_metadata
  - mcp__figma__get_design_context
  - mcp__figma__get_screenshot
  - mcp__figma__get_variable_defs
---

# Figma UI 还原

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
还原契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`

冲突时停止、说明、等澄清，不折中。

## 适用范围

- `/t-figma <figma-url> <target-file>`：把 Figma 设计还原进**已存在**的目标前端文件
- 还原后用 getComputedStyle 数值测量评估还原度（非看截图猜）
- **栈无关**：React/Vue/Svelte/Liquid/原生 HTML/PHP 等均可，栈由 context 探测声明

不用于：从零生成新文件；从 PRD 文本探索 UI 方向；Flutter（架构预留 `--stack flutter`，未实现）。

两条贯穿原则：

1. **不让 LLM 看截图猜差异，改用数值 delta 驱动收敛**。
2. **"参考已有代码"不是 prompt 提醒，而是实现前显式提取成 `context.md` 落盘**。

## 参数

- `<figma-url>`：形如 `https://www.figma.com/design/<fileKey>/<name>?node-id=<nodeId>`，必须可解析出 fileKey 和 nodeId。
- `<target-file>`：目标项目内已存在的源码文件；校验存在 + 在项目内 + 拒绝 `..`。不限定目录名（不假设一定是 `frontend/src`）。

## 核心约束

- **Figma MCP 只在规格提取阶段调用一次批次**：spec 提取后固化到 `spec.json`，迭代期零 MCP 依赖。
- **强制复用已有资源**：还原 agent 输入是 `spec.json` + `context.md`（非 Figma 链接）；token/动效/组件从 context 选。
- **角色分离**：`figma-restore` 实现，`figma-accept` 只读验收。
- **收敛有界**：`max-iterations` 默认 5。
- **探测失败不静默继续**：栈/dev server/playwright 任一探测失败即终止并给可操作提示。

## Input Contract

- Figma URL + 目标文件（参数）
- `${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/figma-restore/index.md`
- Figma Dev Mode MCP（`get_metadata`/`get_design_context`/`get_screenshot`/`get_variable_defs`）；缺失即终止并提示安装

## Output Contract

遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`：

- `.ai/figma/<id>/spec.json` — Figma 规格快照
- `.ai/figma/<id>/baseline.png` — 基准图
- `.ai/figma/<id>/context.md` — 已有代码上下文（含栈声明）
- `.ai/figma/<id>/conflicts.json` — spec 与项目 token 的机器可读冲突清单
- `.ai/figma/<id>/actual.png` — 实际渲染截图
- `.ai/figma/<id>/delta-report.json` — 测量 delta
- `.ai/quality/figma-restore-<feature>-<YYYYMMDD-HHMMSS>.md` — 验收报告

目标文件代码变更由 `figma-restore` agent 产出。

## 工作流程

### 1. 校验与探测

- 从 URL 正则提取 `fileKey`（`/design/([A-Za-z0-9]+)/`）和 `nodeId`（`node-id=([0-9-]+)`）；失败 → 终止提示用法。
- 校验 `<target-file>` 存在且在项目内；否则终止。
- 探测 Figma MCP 工具可用；缺失 → 终止提示安装。
- 建 `.ai/figma/<id>/`（`<id>` = nodeId）。

### 2. 规格提取（单批次 MCP，后续不重调）

1. 复杂层级先 `get_metadata(fileKey, nodeId)` 定位子节点。
2. `get_design_context(fileKey, nodeId)` 拿布局/排版/颜色。
3. `get_screenshot(fileKey, nodeId)` 存 `baseline.png`。
4. `get_variable_defs(fileKey, nodeId)` 拿当前节点使用的设计令牌。
5. 合成 `spec.json`（`source` 不写时间元数据），把根节点尺寸固化为 `viewport`。`probeSelectors` 从 nodes 选语义元素，生成 `data-figma='<name>'` selector + expect。

### 3. 已有代码 context 提取（栈探测）

委派 `context-curator` 或直接只读扫描，产出 `context.md`：

- **探测目标栈**：按文件扩展名/依赖声明/配置文件识别（`.jsx`/`package.json`→react，`.vue`→vue，`.liquid`→shopify，`.php`→php，纯 `.html`→html...）；探测不出标 `unknown`，终止并请人类在 context 声明。
- **扫 design token**：按探测到的栈找（tailwind.config / CSS `:root` vars / `theme.liquid` / theme 文件 / inline style）。
- **扫动效**：`transition`/`@keyframes`/动效库变体（framer-motion / motion-one / GSAP / CSS），带来源路径。
- **扫可复用组件**：同模块优先。
- 按契约 context.md Structure 落盘；章节缺失写「无」。

这是「参考已有代码」的硬产物。

### 4. 还原实现（委派 figma-restore）

按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 委派，prompt 含：

```text
模式: INITIAL_RESTORE
feature: <id>
spec: .ai/figma/<id>/spec.json
context: .ai/figma/<id>/context.md
target_file: <target-file>
agent_spec: ${CLAUDE_PLUGIN_ROOT}/agents/figma-restore.md
```

还原 agent 编辑目标文件，强制复用 context 的 token/动效/组件，为每个 probe 打 `data-figma` 锚点，完成后跑该栈的验证。

### 5. 测量收敛（委派 figma-accept）

确认 context 声明的 dev server 已起、URL 可访问。委派 `figma-accept`，prompt 含：

```text
feature: <id>
spec: .ai/figma/<id>/spec.json
context: .ai/figma/<id>/context.md
target_url: <dev-server-url>
measure_script: ${CLAUDE_PLUGIN_ROOT}/scripts/figma-measure.py
measure_cwd: <能 resolve playwright 的目录>
conflicts: .ai/figma/<id>/conflicts.json
agent_spec: ${CLAUDE_PLUGIN_ROOT}/agents/figma-accept.md
max_iterations: 5
```

`figma-accept` 跑测量脚本、判收敛。

**收敛循环**：

- 有 FAIL/MISSING/ERROR 且未达上限：FAIL 项结构化文本回传，本 skill 以 `模式: CONVERGENCE` 再委派 `figma-restore` 修正，再复测。
- 收敛（阻塞项清零）：产报告（`CONVERGED`），结束。
- 用尽迭代：产报告（`EXHAUSTED`），交人类，结束。

回环禁止：重调 MCP；截图作为 diff 依据；无迭代上限。

### 6. 收尾

报告：结论 / delta 摘要 / baseline 与 actual 路径（视觉辅助）/ CONFLICT 项（交设计师）/ 下一步建议。

## 失败处理

- URL 无法解析 → 提示格式。
- 目标文件不存在/越界 → 提示须已存在且在项目内。
- MCP 工具缺失 → 提示安装 Figma Dev Mode MCP。
- MCP 调用失败（速率/网络）→ 报告；spec 未固化则不继续。
- 栈探测为 `unknown` → 终止，请人类在 context 声明栈。
- dev server 未起/URL 不可访问 → 终止，提示按 context 声明的方式启动。
- 目标项目未装 playwright → 终止，提示在 `measure_cwd` 装 playwright。
- 还原 agent 报验证失败 → 不进入测量，证据交人类。
- 测量连续 MISSING 整批 → 通常 `data-figma` 锚点未打或 selector 错；终止提示检查。

## 附加资源

- 契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`
- 还原 agent：`${CLAUDE_PLUGIN_ROOT}/agents/figma-restore.md`
- 验收 agent：`${CLAUDE_PLUGIN_ROOT}/agents/figma-accept.md`
- 测量脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/figma-measure.py`
- 还原规范：`${CLAUDE_PLUGIN_ROOT}/guides/figma-restore/index.md`
- 测量法：`${CLAUDE_PLUGIN_ROOT}/guides/figma-restore/measurement.md`
