# getComputedStyle 测量法

解释 `/t-figma` 如何用数值测量替代视觉比较判定还原度。delta 阈值与收敛判据的单一真相源是 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`。

## 为什么不用截图对比

截图对比循环（build → screenshot → compare → iterate）失败率最高：

- **LLM 空间推理弱**：看不出 4px 偏移、字重 500 vs 600，会漏明显错误甚至幻觉多余元素。
- **字体渲染差异**：Figma 抗锯齿/字体度量跟浏览器不同，「正确」实现看着也像错的。
- **间距幻觉**：spec 写 16px，生成 13px 还嘴硬「视觉匹配」。

改用：**Playwright 量实际渲染值算 delta，把 delta 作为结构化文本喂给 agent**。

## getComputedStyle

浏览器原生 DOM API（非任何库）。`getComputedStyle(el)` 返回元素所有 CSS 属性的**计算值**——经继承/层叠/`var()` 解析/单位换算后的最终生效值，非源码值。

```js
const cs = getComputedStyle(document.querySelector('.title'));
cs.fontSize;   // "16px"          （源码 1rem 已解析）
cs.color;      // "rgb(29,78,216)" （源码 var(--primary) 已解析）
```

配套 `getBoundingClientRect()` 拿几何尺寸。对比来源：

| 来源 | 值 | 性质 |
|---|---|---|
| Figma MCP `get_design_context` | "font-size:24px" | 设计**意图** |
| 浏览器 `getComputedStyle` | "font-size:28px" | **实际渲染** |

做差 = delta，比看截图猜准一个数量级。

## 探针选择器策略

探针是 `spec.json.probeSelectors` 的声明，告诉脚本「量哪个元素的哪些属性」：

```json
{ "name": "title", "selector": "[data-figma='title']", "expect": { "fontSize": 24, "fontWeight": 600 } }
```

选择器优先级：

1. **`data-figma='<name>'` 属性（首选）**：还原时给被测元素打属性，selector 用属性选择器。栈无关、稳定、语义清晰。
2. **结构化 CSS 选择器（回退）**：元素无法打属性时（如第三方组件内部），用 `[data-testid='x'] h2` 组合。
3. **禁用脆弱选择器**：`:nth-child`、长 class 链、依赖具体框架类名的选择器（重构即失效）。

还原 agent 必须为每个声明 probe 打对应 `data-figma` 锚点，否则测量整批 MISSING。

## delta 阈值（摘要）

完整定义见 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`。

| 类别 | PASS | WARN | FAIL |
|---|---|---|---|
| 数值 | delta < 2px | 2 ≤ delta < 4px | delta ≥ 4px |
| 颜色 | 完全匹配 | — | 不匹配 |
| 时序 | 完全匹配 | delta < 50ms | delta ≥ 50ms |
| 枚举 | 完全匹配 | — | 不匹配 |

依据：

- **2px PASS 边界**：浏览器亚像素渲染与 Figma 字体度量固有差异通常 < 2px，更严陷于噪声。
- **4px FAIL 边界**：4px 是人眼可明确感知的偏差，低于此多为渲染差异。
- **颜色/枚举完全匹配**：离散值无「接近」一说。
- **时序 50ms WARN**：人眼对 < 50ms 几乎无感，但 design system 一致性要求最终对齐。

## 收敛判据

- **收敛成功**：FAIL/MISSING/ERROR 均为零。MISSING 和 ERROR 阻塞（测量不完整）。
- **WARN / CONFLICT 不阻塞**：但必须列入报告；CONFLICT 来自 `conflicts.json` 中已确认的项目 token 取舍。
- **用尽迭代**：达 `max-iterations`（默认 5）仍有阻塞 → 报告交人类。通常 3-5 次收敛；超 8 次说明结构有问题（缺 token / 组件映射错 / Figma 文件太复杂）。

## 回环禁止

- 截图作 diff 依据。
- 重调 Figma MCP。
- 无 `max-iterations` 上限。
- 实现者自判收敛（`figma-restore` 实现，`figma-accept` 裁判，角色分离）。

## 测量脚本

`${CLAUDE_PLUGIN_ROOT}/scripts/figma-measure.py`：

- 仅 Python 标准库，subprocess 调目标项目的 `node` + `playwright`，不引入插件级依赖。
- 内联 JS probe 通过 `page.evaluate` 跑 getComputedStyle + getBoundingClientRect。
- 输出 `delta-report.json`，由 `figma-accept` 解读。

`--cwd` 指向能 resolve `playwright` 的目录（项目根 / frontend 子目录 / 独立 e2e 目录），缺失时报清晰安装提示。调用方式见 `${CLAUDE_PLUGIN_ROOT}/agents/figma-accept.md`。
