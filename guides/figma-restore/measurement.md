# getComputedStyle 测量法

解释 `/t-figma` 如何用数值测量替代视觉比较判定还原度。delta 阈值与收敛判据的单一真相源是 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`。

## 为什么不用截图对比

截图对比循环（build → screenshot → compare → iterate）失败率最高：

- **LLM 空间推理弱**：看不出 4px 偏移、字重 500 vs 600，会漏明显错误甚至幻觉多余元素。
- **字体渲染差异**：Figma 抗锯齿/字体度量跟浏览器不同，「正确」实现看着也像错的。
- **间距幻觉**：spec 写 16px，生成 13px 还嘴硬「视觉匹配」。

改用：**Playwright 量实际渲染值算 delta，把 delta 作为结构化文本喂给 agent**。边界：拒绝的是让 LLM 看图判定；`--pixel-diff` 的程序化像素统计（代码算数字）作为 advisory 信号进报告是允许的。

## getComputedStyle

`getComputedStyle(el)` 返回计算值——继承/层叠/`var()` 解析/单位换算后的最终生效值；`getBoundingClientRect()` 提供几何与位置（`width/height/x/y`）。Figma spec 值是设计意图，浏览器实测是实际渲染，做差 = delta，比看截图猜准一个数量级。

- **位置也测**：`x`/`y` 是 viewport 相对坐标。没有位置判据时，整体错位、列序颠倒能靠单元素样式 PASS 混过去；spec 只为稳定布局锚点生成位置探针，`fixed`/`sticky` 不生成。
- **简写全量判定**：`padding`/`margin`/`gap`/`borderRadius` 简写展开为四边/行列/四角子项分别判定，`padding: 8px 24px` 这类非对称错误不漏；也可直接写长边属性只测单侧。

## 探针选择器策略

探针是 `spec.json.probeSelectors` 的声明，告诉脚本「量哪个元素的哪些属性」：

```json
{ "name": "title", "selector": "[data-figma='title']", "expect": { "fontSize": 24, "x": 16, "y": 24 } }
```

选择器优先级：

1. **`data-figma='<name>'` 属性（首选）**：还原时给被测元素打属性，selector 用属性选择器。栈无关、稳定、语义清晰。
2. **结构化 CSS 选择器（回退）**：元素无法打属性时（如第三方组件内部），用 `[data-testid='x'] h2` 组合。
3. **禁用脆弱选择器**：`:nth-child`、长 class 链、依赖具体框架类名的选择器（重构即失效）。

还原 agent 必须为每个声明 probe 打对应 `data-figma` 锚点，否则测量整批 MISSING。

## 测量稳定性

取值前依次：等 `document.fonts.ready`（5s 上限，避免 fallback 字体假 delta）；冻结动效（禁 transition/animation、隐藏 caret，Web Animations 有限动画快进/无限取消；declared duration 仍可测）；每选择器 attach 等 3s（消除 SPA 水合假 MISSING）；`networkidle` 等 5s，超时写 `meta.networkidle`。JS 动效库驱动的元素可能未到终态，靠 meta 与截图人工判断。

## delta 阈值（摘要）

完整定义见 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`。

| 类别 | PASS | WARN | FAIL |
|---|---|---|---|
| 数值（含 x/y 与展开子项） | delta < 2px | 2 ≤ delta < 4px | delta ≥ 4px |
| 颜色 | 完全匹配 | 不支持的格式（渐变/display-p3/color-mix） | 可解析但不匹配 |
| 时序 | 完全匹配 | delta < 50ms | delta ≥ 50ms |
| 枚举 | 完全匹配 | lineHeight 一边为 `normal` | 不匹配 |

依据：2px 内是浏览器/Figma 渲染噪声；4px 起人眼可明确感知；离散值无「接近」；机器无法判定的格式（渐变、`normal` 行高）降 WARN 交人工；时序 50ms 内人眼无感。

## 像素 diff 兜底

探针外的偏差（多余/缺失元素等）机器不校验。`--pixel-diff` 用 pixelmatch（AA 忽略 + 感知色距）比对 baseline/actual，输出 `diffRatio`、可视化图和 ≥5% 提示标记，只进报告不进回环。Figma 与浏览器渲染的系统性差异 + 尺寸对齐缩放决定它只能是 advisory。需 `pip install pixelmatch Pillow`，缺依赖自动降级 skipped，不影响测量。

## 探针覆盖率

spec 声明 `probeableNodes` 时报告输出 `coverage.ratio`；低于 80% 标提示——未覆盖元素靠人工复核 baseline/actual。

## 收敛判据

- **收敛成功**：FAIL/MISSING/ERROR 为零（多断点全部清零）；MISSING/ERROR 阻塞（测量不完整）。
- **WARN/CONFLICT 不阻塞**，必须列入报告；advisory 信号（像素 diff/覆盖率/完整性）只列不判。
- **用尽迭代**：达 `max-iterations`（默认 5）→ 报告交人类。通常 3-5 次收敛；超 8 次说明结构有问题（缺 token / 组件映射错 / Figma 文件太复杂）。

每轮测量带 `--iteration <N>`：报告归档 `iterations/iter-<N>.json`，用尽迭代时可复盘每轮 delta 变化。

## 回环禁止

- 以截图或像素 diff 结果驱动回环修正（advisory 信号只进报告）。
- 重调 Figma MCP。
- 无 `max-iterations` 上限。
- 实现者自判收敛（`figma-restore` 实现，`figma-accept` 裁判，角色分离）。

## 测量脚本

`${CLAUDE_PLUGIN_ROOT}/scripts/figma-measure.py`：Python 标准库（`--pixel-diff` 可选依赖 pixelmatch/Pillow），subprocess 调目标项目 `node` + `playwright`，内联 JS 先做稳定化再探针。`spec.viewport` 支持断点数组（每项可带 `name`/`probes`；主断点截图 `actual.png`，其余 `actual-<name>.png`）；`--iteration` 归档每轮报告；`--pixel-diff` 输出 advisory 像素比对。

`--cwd` 指向能 resolve `playwright` 的目录（项目根 / frontend 子目录 / 独立 e2e 目录），缺失时报安装提示。调用方式见 `${CLAUDE_PLUGIN_ROOT}/agents/figma-accept.md`。
