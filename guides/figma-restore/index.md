# Figma UI 还原规范入口

按「先定位问题，再读对应页面」使用。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| 还原工作模式、token 复用、动效对齐、栈适配 | 本页下方 |
| getComputedStyle 测量法、探针策略、delta 阈值 | [measurement.md](${CLAUDE_PLUGIN_ROOT}/guides/figma-restore/measurement.md) |
| 产物结构、source-of-truth、收敛循环 | [figma-restore-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md) |
| 还原执行者的执行顺序与门禁 | [figma-restore.md](${CLAUDE_PLUGIN_ROOT}/agents/figma-restore.md) |
| 只读测量验收者的执行流程 | [figma-accept.md](${CLAUDE_PLUGIN_ROOT}/agents/figma-accept.md) |

## 使用规则

- 只覆盖 Figma → 已有代码的还原与测量。不重新定义目标栈的架构真相（React/Vue/Tailwind 等以目标项目对应 guide 为准）。
- delta 阈值与收敛判据单一真相源是 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md`，本目录只解释执行方法。

## 工作模式

Figma UI 还原不是「读设计 → 生成代码」单向流，而是「读设计 → 参考已有代码 → 实现 → 测量 → 回环」闭环。两个反直觉点：

1. **Figma MCP 只在规格提取阶段调用一个批次**。spec 提取后固化到 `spec.json`，迭代零 MCP 依赖。原因：重复提取可能得到不同上下文，导致迭代基准漂移，也会额外消耗 MCP 配额。
2. **不让 LLM 看截图猜差异**。视觉像素比较是 LLM 最不擅长的事。改用 getComputedStyle 量实际值算 delta，让 LLM 干「读数字改数字」的活。

## Design Token 复用

**每个 spec 视觉值，先在 `context.md` 找映射，找不到才用字面值。**

- spec 颜色 `#1d4ed8` → 用 context 的 `primary-500` token，不写任意值 `bg-[#1d4ed8]`。
- spec 间距 13px，token 只有 12/16 → 选 `space-3`(12px)，delta 1px 落 PASS；不为消除 1px 差异引入任意值。
- spec 值与 token 冲突无法近似 → 保持 token，标 CONFLICT 交人类裁决是否扩 token。

核心权衡：**像素级 spec 值服从 design system token**。零散任意值会在主题切换/响应式/维护中失效。

## 动效对齐

动效（transition/animation/动效库变体）从 `context.md` 声明的模式中选，不引入新 duration/easing。

- context 声明「过渡统一 200ms ease-out」→ spec 的 250ms 实现用 200ms，delta 50ms 在 WARN，不阻塞收敛。
- spec 声明项目没有的新动效 → 标记交设计师确认，不在还原阶段擅自新增。

## 可复用组件优先

`context.md` 声明的组件必须用，不重写等价实现。spec 出现卡片 → 用声明的 `<Card>`；视觉略异通过 props/variant 调，而非新组件。只有 context 明确没有时才新增，并在 `components_added` 声明。

## 栈适配

t-figma **栈无关**，按 `context.md`「目标栈」声明工作：

- **token 来源**按栈找：tailwind.config / CSS `:root` vars / `theme.liquid` / theme 文件 / inline style。
- **动效来源**按栈找：CSS transition/@keyframes / framer-motion / motion-one / GSAP / Liquid schema。
- **组件单位**按栈表达：React 组件 / Vue SFC / Svelte 组件 / Liquid snippet / PHP partial / 原生 HTML 片段。
- **验证命令**按栈定（见 `figma-restore` agent「完成前验证」）。

栈探测为 `unknown` 时终止，请人类在 context 声明。
