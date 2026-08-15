# t-figma UI 还原度验证方案评估

评估日期：2026-08-14。评估对象：`skills/t-figma/` 及其引用的契约、guide、agent、测量脚本。本文是只读评估报告，不修改任何插件文件，不提交 git。

> **修复记录（2026-08-14）**：P0/P1/P2 已全部落地（「仅 chromium」按第四节结论有意不修），涉及 `scripts/figma-measure.py`、`figma-restore-contract.md`、`measurement.md`、`SKILL.md`、`figma-accept.md`、`figma-restore.md` 及测试（71 用例全绿）。其余内容保留评估时点原状。

## 结论

**核心路线正确且领先，实现层有三个结构性盲区，修复成本都不高。**

1. **「数值 delta 驱动收敛、拒绝 LLM 看截图猜差异」这一根本取舍是成立的**，且优于业界多数做法。独立工程实践（[vadim.blog 的 Playwright 测量法](https://vadim.blog/pixel-perfect-playwright-figma-mcp/)，与 t-figma 思路同源）和学术研究（[MLLM as a UI Judge](https://arxiv.org/html/2510.08783v1)：多模态 LLM 判 UI 成对偏好准确率仅 59-60%，细粒度差异判断接近随机）都支撑这个方向。角色分离（实现 vs 只读裁判）、spec 固化后零 MCP、资产 SHA-256 完整性链，在同类方案里是亮点。
2. 但「不拿截图当 diff 依据」的原则被过度延伸成了「完全不做程序化像素对比」。业界主流的截图 diff 是**代码算数字**（pixelmatch/ODiff 带 AA 忽略和感知色距），不是 LLM 看图。当前方案缺一层像素级整页兜底信号，探针没覆盖到的错误（多余/缺失元素）没有任何机器判据。
3. **当前测量有系统性漏判**：脚本不比较元素位置（x/y），padding/margin 只测 top 一边、圆角只测左上角——元素整体错位、列序颠倒、非对称间距全部 PASS。
4. **测量时机不稳定**：不等 `document.fonts.ready`、不冻结动画、`networkidle` 超时静默吞掉。字体未加载时测到的是 fallback 字体值（假 FAIL），SPA 水合未完成时锚点批量 MISSING（假缺失）。这些正是 Playwright/商业视觉回归工具花了大力气解决的抗抖动问题。

## 一、现状梳理

t-figma 的验证链路（依据 SKILL.md、figma-restore-contract.md、measurement.md、figma-measure.py）：

```text
Figma MCP 单批次提取 → spec.json 固化（nodes/tokens/assets/probeSelectors/viewport）
→ context.md（栈/token/动效/组件/资产约定）
→ figma-restore 实现（data-figma 锚点，spec 值优先映射项目 token）
→ figma-measure.py（Python 标准库 + 目标项目 Playwright）
   goto(domcontentloaded) → networkidle(5s, 超时静默忽略) → page.evaluate
   getComputedStyle + getBoundingClientRect 逐探针取值 → delta-report.json
→ figma-accept 只读判收敛：FAIL/MISSING/ERROR=0 即 CONVERGED，最多 5 轮
→ 资产：SHA-256 manifest + 页面加载（naturalWidth>0）
→ baseline.png/actual.png 仅交人类复核，不参与机器判定
```

判定阈值（契约 Delta Thresholds）：

| 类别 | PASS | WARN | FAIL |
|---|---|---|---|
| 数值（fontSize/width/height/padding/margin/gap/borderRadius） | delta < 2px | 2 ≤ delta < 4px | delta ≥ 4px |
| 颜色 | 完全匹配 | — | 不匹配 |
| 时序 | 完全匹配 | delta < 50ms | delta ≥ 50ms |
| 枚举（fontWeight/opacity/lineHeight） | 完全匹配 | — | 不匹配 |

脚本实际测量逻辑（figma-measure.py `PROBE_JS_TEMPLATE_WITH_BOOT`）：

- `width/height` 取 `getBoundingClientRect()`；
- `padding` 只取 `parseFloat(cs.paddingTop)`，`margin` 只取 `parseFloat(cs.marginTop)`，`borderRadius` 只取 `borderTopLeftRadius`；
- `gap` 取 `parseFloat(cs.gap)`——注意 row-gap ≠ column-gap 时 `cs.gap` 返回空串，`parseFloat` 得 `NaN`，经 `JSON.stringify` 序列化为 `null`，会被判 MISSING 而非 FAIL；
- 颜色做 hex/rgb/rgba 归一化后全等比较；CONFLICT 项由 conflicts.json 精确匹配豁免。

## 二、业界方案对比

| 方案 | 比对方式 | 优势 | 对 design-to-code 的适用性 |
|---|---|---|---|
| **Playwright `toHaveScreenshot`** | code-to-code 基线截图，逐像素 YIQ 感知色距（threshold 0.2）+ `maxDiffPixels` | 抗抖动工程最完整：默认 `animations:'disabled'`、`caret:'hide'`、`scale:'css'`、`mask`/`stylePath` 遮蔽动态区、连续两次截图一致才比较 | **不适用**：基线是历史代码渲染，验证不了「是否符合设计稿」（[vadim.blog 明确指出这一点](https://vadim.blog/pixel-perfect-playwright-figma-mcp/)）。但它的确定性细节值得 t-figma 吸收 |
| **Percy / Chromatic / Applitools** | 云端 DOM 快照重渲染 + diff；Intelli-ignore / match levels / AI diff 降误报 | 覆盖率 100%，误报治理成熟（见 [Sparkbox 对比](https://sparkbox.com/foundry/visual_regression_testing_with_backstopjs_applitools_webdriverio_wraith_percy_chromatic)、[Crosscheck 2026 对比](https://crosscheck.cloud/blogs/percy-vs-applitools-vs-chromatic-visual-regression-testing/)） | 同样是 code-to-code 回归；引云依赖违背插件零依赖原则。**不引入**，其「遮蔽动态区域而非放宽全局阈值」的思路可借鉴 |
| **pixelmatch / ODiff**（本地像素 diff 库） | 逐像素感知色距 + **抗锯齿像素检测忽略**（pixelmatch `includeAA`）；ODiff SIMD 高性能 + ignore regions | 纯代码判定、无 LLM 参与、AA 噪声免疫 | **适合做兜底信号**：actual.png vs baseline.png 出 diff 比例，补探针覆盖盲区。但 Figma 渲染与浏览器渲染存在系统性字体/AA 差异，只能作松阈值的 advisory，不能阻塞收敛 |
| **数值测量法（vadim.blog，与 t-figma 同思路）** | Playwright 当「测量仪器」，getComputedStyle/getBoundingClientRect 与 Figma 规格做差 | 实战验证有效：「effective because of the measurement layer, not because of the AI layer」；AI 幻觉（重复图标）只有 spec 对比能发现 | **就是 t-figma 的路线**。其暴露的痛点 t-figma 大多已有对策（MCP 速率限制→单批次提取；token 名陷阱→强制复用 context token），但「Playwright 静默失败」类风险 t-figma 也存在 |
| **Pix skill（Claude Code 生态同类）** | Recon/Code/Refine 多阶段，浏览器渲染 vs Figma 截图对比 + getComputedStyle 数值审计（[MCPMarket](https://mcpmarket.com/tools/skills/pixel-perfect-ui-implementation)） | 闭环全自动 | 混合路线（截图对比参与回环），恰是 t-figma 刻意回避的：让 LLM 看两图找差异，可靠性无保证 |
| **多模态 LLM 打分** | 给两图让模型输出一致性分数 | 无需基础设施 | **研究证伪其末端可靠性**：[MLLM as a UI Judge](https://arxiv.org/html/2510.08783v1) 显示成对偏好仅 ~60%（差异大时 90%+，细粒度接近随机），结论是「适合早期低风险筛选，不适合末端验证」。t-figma 拒绝它是正确决策，且与「最终人类视觉复核」定位互补 |
| **OverlayQA 等叠加核对** | 设计稿半透明叠加人工核对（[overlayqa.com](https://overlayqa.com/blog/pixel-perfect-design/)） | 人类验收体验好 | 与 t-figma 的「人类复核 baseline/actual」环节等价，可作验收报告的呈现方式参考 |

**对比结论**：业界把「确定性比对」和「LLM 视觉判断」分得很清——前者（像素 diff、DOM diff、数值 diff）广泛使用，后者一致被认为是弱项。t-figma 拒绝的是后者（正确），但把前者里的像素 diff 也一起拒了（过度）。

## 三、差距与风险

按严重程度排序。前三项会系统性漏判/误判，建议按 P0 处理。

### P0-1 位置与布局结构不测量

`rect.x/y` 从不参与比较。后果：元素整体偏移、两列顺序颠倒、垂直堆叠顺序错、绝对定位错位——只要每个元素自身的字号/颜色/尺寸对，全部 PASS。而 Figma 的 `nodes[].layout` 本来就带坐标信息，spec 里现成可用。这是当前方案最大的正确性缺口。

### P0-2 简写属性只测单边

`padding` = `paddingTop`、`margin` = `marginTop`、`borderRadius` = 左上角。`padding: 8px 24px` 的水平方向错误、四角不一致的圆角全部漏判。修复是脚本内几行的事。

### P0-3 测量时机不稳定

- 字体：不等 `document.fonts.ready`，webfont 未加载时 `fontSize/lineHeight` 测的是 fallback 字体的度量 → 假 FAIL 驱动无效回环；Playwright 截图断言默认等字体，t-figma 没等。
- 动画/过渡：入场动画进行中的元素，computed style 反映动画中间态；`transitionDuration` 能测但视觉状态不可复现。
- 加载：`waitUntil:'domcontentloaded'` 后立即查询，SPA（React/Vue 水合后渲染）可能查不到锚点 → 整批假 MISSING（SKILL.md 把「连续 MISSING」归因为锚点未打，但时序问题同样会产生这个症状，误导排查方向）。
- `networkidle` 5s 超时被 `.catch(() => {})` 静默吞掉，报告里无任何痕迹。

同一页面两次测量可能得出不同 delta-report，收敛判定本身不可复现——这在业界被视为视觉测试的第一等公民问题（参考 [Argos 的稳定化实践](https://argos-ci.com/blog/screenshot-stabilization)、[houseful 的 Playwright 抗抖动实践](https://houseful.blog/posts/2023/fix-flaky-playwright-visual-regression-tests/)）。

### P1-1 探针覆盖率无保证

只有 `probeSelectors` 声明的元素被测量。spec 提取阶段「从 nodes 选语义元素」生成探针，选多少、漏多少没有度量；还原 agent 漏实现一个无探针的元素、或凭空多加一个元素（vadim.blog 实测的「重复图标」幻觉），机器完全无感知。delta-report 里没有「本次测量覆盖了 spec 的多少节点」这个数。

### P1-2 无像素级整页兜底

当前唯一的全局性机器检查是资产加载。整页层面的偏差（探针之外的一切）只有人类对照 baseline/actual 一条路。一层松阈值的程序化像素 diff（pixelmatch，AA 忽略）可以把「多余元素/缺失元素/整体错位」变成一个数字信号进报告，且完全不违背「不让 LLM 看截图」原则——是代码在算，不是模型在看。

### P1-3 属性归一化缺口

- `lineHeight` 按枚举全等比较：Figma 自动行高（百分比/auto）在浏览器计算值可能是 `normal` 或换算 px，必假 FAIL。spec 生成端应跳过 auto 行高的该项，或测量端归一化。
- 颜色只支持 sRGB hex/rgb：Figma 的 display-p3 填充、渐变 fill 未处理，归一化失败直接 FAIL。
- `gap` 非对称时如上所述变 MISSING。

### P2（记录在案，暂不动）

- 单 viewport：无响应式多断点测量（契约已有单 viewport 概念，可扩展数组）。
- 仅 chromium：还原度验收场景可接受，跨浏览器属回归测试职责，不是本 skill 目标。
- delta-report 只留最后一轮，无趋势；对调试「为什么用尽 5 轮」略有价值。
- spec 端完整性：`get_design_context` 复杂层级截断/漏节点无对照检查（可用 `get_metadata` 的节点数做粗校验）。

## 四、改进建议（按优先级）

以下每条注明唯一落点文件，遵循「阈值/契约改 protocol，方法解释改 guide，逻辑改脚本」的仓库边界。

### 1. 补位置测量 — P0，figma-measure.py + 契约

- `PROBE_JS_TEMPLATE_WITH_BOOT` 增加 `x/y` 取 `rect.x/rect.y`；spec 端（SKILL.md stage 2）生成探针时把 Figma `absoluteBoundingBox` 换算成同 viewport 坐标写入 expect。
- `protocols/figma-restore-contract.md` Delta Thresholds 增加「位置」类别，阈值沿用数值档（<2px PASS），整页滚动容器内的相对定位可豁免标注。
- `guides/figma-restore/measurement.md` 同步说明。

### 2. 四边/四角全量比较 — P0，figma-measure.py

`padding/margin` 拆四边逐一比较（任一边超阈值即按该项计），`borderRadius` 同理四角；`gap` 改读 `rowGap/columnGap`。probe 的 expect 不需要变，纯脚本侧增强。

### 3. 测量稳定化 — P0，figma-measure.py

- `goto` 后 `await document.fonts.ready`（带超时上限）。
- 注入样式冻结动画：`* { animation-play-state: paused !important; transition: none !important; caret-color: transparent }`（比 Playwright `animations:'disabled'` 更彻底，且不依赖 test runner）。
- 探针查询加 `waitForSelector` 重试窗（如 3s），消除水合时序导致的假 MISSING。
- `networkidle` 超时不再静默：在 delta-report 里记 note，报告可见。

### 4. 像素 diff 兜底信号 — P1，figma-measure.py + 契约 + figma-accept.md

- 新增可选 `--pixel-diff`：对 actual.png 与 baseline.png 跑 pixelmatch（[PyPI 有 Python port](https://pypi.org/project/pixelmatch/)，默认开 `AA` 忽略），输出 `diffRatio` + diff 可视图。
- 定位是 **advisory 信号**：写入 delta-report 单独字段和验收报告章节，不进收敛判据（Figma 与浏览器的字体渲染/AA 差异是系统性的，硬阈值会假阳性爆炸）。建议 `diffRatio ≥ 5%` 才在报告里标 ⚠ 提示人类重点复核。
- `agents/figma-accept.md` 报告结构加「像素 diff 概览」一节，措辞明确「布局样式仍以 delta 为准」。
- 契约「回环禁止」条款同步改写：禁止的是**以截图 diff 驱动回环**和 LLM 看图判定，程序化像素统计作为报告信号不在此列——把这条边界写清楚，避免后人误读。

### 5. 探针覆盖率指标 — P1，SKILL.md + figma-measure.py + figma-accept.md

- spec 生成时记录 `spec.nodes` 总数与 `probeSelectors` 覆盖数；delta-report summary 增加 `probeCoverage`。
- `figma-accept` 报告必须呈现覆盖率；低于阈值（建议 80% 的文本/容器类节点）时在报告中标提示，不阻塞。

### 6. 属性归一化 — P1，figma-measure.py + SKILL.md

- spec 生成端：Figma 自动行高不生成 lineHeight 探针项；渐变/p3 颜色跳过并记录 note。
- 测量端：`gap` 改 `rowGap/columnGap`（见建议 2）。

### 7. 不建议做的

- **不引入 Percy/Chromatic/Applitools**：云依赖 + code-to-code 定位，与插件零依赖、design-to-code 目标错位。
- **不改成 LLM 视觉打分收敛**：研究数据（成对 ~60%）不支持；现有「人类最终复核」已经是该技术的正确用法。
- **不追跨浏览器**：还原度验收 chromium 单浏览器足够，跨浏览器是目标项目自己回归测试的职责。
- **不把像素 diff 升格为硬门禁**：Figma 渲染 vs 浏览器渲染的系统性差异决定了它只能是 advisory。

## 参考来源

- [vadim.blog — Pixel-perfect UI with Playwright + Figma MCP](https://vadim.blog/pixel-perfect-playwright-figma-mcp/)（数值测量法实战与 AI 幻觉案例）
- [arXiv 2510.08783 — MLLM as a UI Judge](https://arxiv.org/html/2510.08783v1)（多模态 LLM 判 UI 的可靠性数据）
- [Playwright — PageAssertions API](https://playwright.dev/docs/api/class-pageassertions)（`toHaveScreenshot` 确定性选项全集）
- [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch)、[dmtrKovalenko/odiff](https://github.com/dmtrKovalenko/odiff)（AA 忽略与感知色距）
- [Sparkbox — 六工具实战对比](https://sparkbox.com/foundry/visual_regression_testing_with_backstopjs_applitools_webdriverio_wraith_percy_chromatic)、[Crosscheck — Percy vs Applitools vs Chromatic 2026](https://crosscheck.cloud/blogs/percy-vs-applitools-vs-chromatic-visual-regression-testing/)
- [Argos — Screenshot Stabilization](https://argos-ci.com/blog/screenshot-stabilization)、[houseful — Fixing flaky Playwright visual regression tests](https://houseful.blog/posts/2023/fix-flaky-playwright-visual-regression-tests/)
- [MCPMarket — Pix: Pixel-Perfect UI Claude Code Skill](https://mcpmarket.com/tools/skills/pixel-perfect-ui-implementation)、[OverlayQA — Pixel-Perfect Design](https://overlayqa.com/blog/pixel-perfect-design/)
