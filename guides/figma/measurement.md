# Figma UI 测量与验收

delta 阈值和收敛判据的单一真相源是 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`。

`getComputedStyle()` 提供层叠后的最终样式，`getBoundingClientRect()` 提供 width/height/x/y。实现必须给被测元素稳定的 `data-figma` 锚点；禁止用易变的生成类名或 `nth-child` 作为首选探针。

整页 impl 输出全页 actual；局部 fix 同时声明 `scopeSelector`，Playwright 对该元素截图，使 baseline 和 actual 覆盖同一视觉区域。截图与 pixel diff 可发现错误分组、裁切和 stacking，但具体修改应落为 spec revision、探针 delta 或明确的代码证据。

测量前等待 webfont 和必要资源，冻结动画，记录 networkidle。每个 viewport 独立判定；FAIL/MISSING/ERROR 清零后才收敛。资产内容、合成文字和视频播放仍需资源完整性、加载状态、Range 请求与人工视觉证据共同确认。
