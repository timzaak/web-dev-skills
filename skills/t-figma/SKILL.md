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
  - mcp__figma__download_assets
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
- `${CLAUDE_PLUGIN_ROOT}/guides/figma-restore/assets.md`（资产下载与落位执行法）
- Figma MCP 核心工具（`get_metadata`/`get_design_context`/`get_screenshot`/`get_variable_defs`）；remote MCP 的 `download_assets` 按需使用

## Output Contract

遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`：

- `.ai/figma/<id>/spec.json` — Figma 规格快照（含 `assets` 节点清单、`probeableNodes`、`integrity`；响应式时 `viewport` 为断点数组）
- `.ai/figma/<id>/baseline.png` — 基准图
- `.ai/figma/<id>/context.md` — 已有代码上下文（含栈声明 + 资产目录声明）
- `.ai/figma/<id>/conflicts.json` — spec 与项目 token 的机器可读冲突清单
- `.ai/figma/<id>/raw/` — MCP 临时 URL 对应的原始字节（有资产时创建，可清理）
- `.ai/figma/<id>/assets-manifest.json` — Figma 资产 → 最终 outputPath + SHA-256 映射
- `.ai/figma/<id>/actual.png` — 实际渲染截图（主断点；多断点时其余为 `actual-<name>.png`）
- `.ai/figma/<id>/delta-report.json` — 测量 delta（最后一次；含 coverage/meta/pixelDiff）
- `.ai/figma/<id>/iterations/` — 每轮收敛迭代的报告归档（`iter-<N>.json`，可清理）
- `.ai/figma/<id>/pixel-diff.png` — 可选：advisory 像素 diff 可视图（`--pixel-diff` 时）
- `.ai/quality/figma-restore-<feature>-<YYYYMMDD-HHMMSS>.md` — 验收报告

目标文件代码变更由 `figma-restore` agent 产出。

## 工作流程

### 1. 校验与探测

- 从 URL 正则提取 `fileKey`（`/design/([A-Za-z0-9]+)/`）和 `nodeId`（`node-id=([0-9-]+)`）；失败 → 终止提示用法。
- 校验 `<target-file>` 存在且在项目内；否则终止。
- 探测 Figma MCP 核心工具可用；缺失 → 终止提示安装。`download_assets` 仅在需要额外导出时按需探测。
- 建 `.ai/figma/<id>/`（`<id>` = nodeId）。

### 2. 规格提取（单批次 MCP，后续不重调）

1. 复杂层级先 `get_metadata(fileKey, nodeId)` 定位子节点。
2. `get_design_context(fileKey, nodeId)` 拿布局/排版/颜色。
3. `get_screenshot(fileKey, nodeId)` 存 `baseline.png`。
4. `get_variable_defs(fileKey, nodeId)` 拿当前节点使用的设计令牌。
5. 从 `get_design_context` 返回内容收集本次实现需要的资产 URL，并立即下载到 `.ai/figma/<id>/raw/`；仅在缺少资产或需要节点导出时按需调用 remote-only `download_assets`，再下载其临时 URL。按 `image|svg|gif` 写入 `spec.json.assets`；命名与失败处理见资产 guide。视频源缺失时终止请人类提供，不假定 MCP 可下载原视频。
6. 合成 `spec.json`（`source` 不写时间元数据）。`viewport`：单断点取根节点尺寸；响应式取各断点写成数组（带 `name`，断点间 expect 不同时生成独立 `probes`）。`probeSelectors` 从 nodes 选语义元素，生成 `data-figma='<name>'` selector + expect：稳定布局锚点（根 frame 直接子级）补 `x`/`y`；四边一致用简写、非对称写长边；Figma 自动行高、渐变/display-p3 颜色不生成项。记录 `probeableNodes` 与 `integrity`（metadata 节点数 vs spec 节点数）。

### 3. 已有代码 context 提取（栈探测）

委派 `context-curator` 或直接只读扫描，产出 `context.md`：

- **探测目标栈**：按文件扩展名/依赖声明/配置文件识别（`.jsx`/`package.json`→react，`.vue`→vue，`.liquid`→shopify，`.php`→php，纯 `.html`→html...）；探测不出标 `unknown`，终止并请人类在 context 声明。
- **扫 design token**：按探测到的栈找（tailwind.config / CSS `:root` vars / `theme.liquid` / theme 文件 / inline style）。
- **扫动效**：`transition`/`@keyframes`/动效库变体（framer-motion / motion-one / GSAP / CSS），带来源路径。
- **扫可复用组件**：同模块优先。
- **扫资产目录与命名约定**：按 `DESIGN.md`（若存在）→目标文件邻近用法→框架明确约定探测；只有存在资产且多个位置无法裁决时才请人类声明，无资产写「不适用」。
- 按契约 context.md Structure 落盘；章节缺失写「无」。

这是「参考已有代码」的硬产物。

context 落盘后，把 raw 原始字节按项目约定放入正式资产目录，计算 SHA-256 并写 `assets-manifest.json`。同名同 hash 复用，同名异 hash 停止请人类选择，禁止静默覆盖。默认不转码；项目 `DESIGN.md` 若有明确约定则按项目规范执行。

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

还原 agent 编辑目标文件，强制复用 context 的 token/动效/组件，为每个 probe 打 `data-figma` 锚点，完成后跑该栈的验证。资产按 manifest 的 `outputPath` 和 context 的引用方式使用，不重新下载或造图。

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
iteration: <当前轮次，从 1 递增；回环复测时 +1>
pixel_diff: auto
agent_spec: ${CLAUDE_PLUGIN_ROOT}/agents/figma-accept.md
max_iterations: 5
```

`figma-accept` 跑测量脚本（带 `--iteration`，`pixel_diff: auto` 时尽力启用 `--pixel-diff`，缺依赖自动降级）、判收敛。

**收敛循环**：

- 有 FAIL/MISSING/ERROR 且未达上限：FAIL 项结构化文本回传，本 skill 以 `模式: CONVERGENCE` 再委派 `figma-restore` 修正，再复测（iteration +1）。
- 收敛（阻塞项清零）：产报告（`CONVERGED`），结束。
- 用尽迭代：产报告（`EXHAUSTED`），交人类，结束。

回环禁止：重调 MCP；以截图或像素 diff 结果驱动回环修正（advisory 信号只进报告）；无迭代上限。

### 6. 收尾

报告：结论 / delta 摘要（含各断点） / 覆盖率 / 像素 diff 概览 / 资产完整性 / baseline 与 actual 路径（资产内容需视觉复核）/ CONFLICT 项（交设计师）/ 测量稳定性 meta（networkidle 等）/ 迭代历史路径（`iterations/`）/ 下一步建议。

## 失败处理

- URL 无法解析 → 提示格式。
- 目标文件不存在/越界 → 提示须已存在且在项目内。
- MCP 工具缺失 → 提示安装 Figma Dev Mode MCP。
- MCP 调用失败（速率/网络）→ 报告；spec 未固化则不继续。
- 栈探测为 `unknown` → 终止，请人类在 context 声明栈。
- dev server 未起/URL 不可访问 → 终止，提示按 context 声明的方式启动。
- 目标项目未装 playwright → 终止，提示在 `measure_cwd` 装 playwright。
- 必需资产 URL 下载失败 → 终止并保留已下载 raw，禁止占位替代。
- 需要额外导出但 remote `download_assets` 不可用 → 终止并说明所需资产；已有 design-context URL 不受影响。
- 同名正式资产 hash 不同 → 终止，请人类选择新名称或确认替换。
- 设计依赖视频但项目没有可用源 → 终止，请人类提供资产或 CDN 地址。
- 还原 agent 报验证失败 → 不进入测量，证据交人类。
- 测量连续 MISSING 整批 → 通常 `data-figma` 锚点未打或 selector 错；终止提示检查。

## 附加资源

- 契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`
- 还原 agent：`${CLAUDE_PLUGIN_ROOT}/agents/figma-restore.md`
- 验收 agent：`${CLAUDE_PLUGIN_ROOT}/agents/figma-accept.md`
- 测量脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/figma-measure.py`
- 还原规范：`${CLAUDE_PLUGIN_ROOT}/guides/figma-restore/index.md`
- 资产下载与落位：`${CLAUDE_PLUGIN_ROOT}/guides/figma-restore/assets.md`
- 测量法：`${CLAUDE_PLUGIN_ROOT}/guides/figma-restore/measurement.md`
