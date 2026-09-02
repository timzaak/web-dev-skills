# Figma 动效交互原则基准

本规范把迪士尼动画十二原则提炼为界面动效的判断标准，供 `t-figma-ux` 在 Figma 原型证据缺失时生成默认候选、并在实现审查时对照。`motion.json` 结构、探针与验收门禁见 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`。

## 证据优先级

1. Figma 原型数据（design context/metadata 携带的 reactions、transition、smart animate 及其 duration/easing）是第一基准。
2. 目标项目现有动效模式（context 收集的组件动效、easing 词表）优先于原则默认。
3. 原则默认只覆盖前两者都没有的交互，且在 `motion.json` 标 `origin: principle-default`。
4. 首屏转场、跨页转场、破坏性操作反馈等影响用户流程感知或品牌调性的缺口必须请开发者裁决后标 `origin: user-decision`，不得静默套用默认。

## 十二原则的界面转译

| 原则 | 界面含义 | 默认应用 |
|---|---|---|
| 挤压与拉伸 | 受击形变反馈 | hover/press 用 `scale(0.96~1.04)`；不得产生破坏布局的形变 |
| 预备动作 | 动作前提示 | 弹层出现前触发器先有 hover/press 态；长任务前按钮先进 pending 态 |
| 演出布局 | 同一时刻只有一个动效主角 | 同屏只保留一个主要动效，其余降为次要反馈或不动 |
| 关键姿态优先 | 先定起止态再补过渡 | 先实现 open/close 等稳定终态，再补过渡；不允许只有过渡没有可达终态 |
| 跟随与重叠 | 余动与错峰 | 列表项 stagger 20–60ms 错峰出入；抽屉完全关闭后才解除滚动锁定 |
| 慢入慢出 | 非匀速运动 | 位移/缩放禁用 `linear`；`linear` 只用于进度条和旋转指示 |
| 弧线运动 | 跨距离移动走曲线 | toast、浮层横移用 transform-origin 或 offset-path；长距离直线平移显得机械 |
| 次要动作 | 辅助反馈不抢主 | 主文案切换时图标微动可叠加；次要动效时长不超过主动效 |
| 时间节奏 | 时长与交互含义匹配 | 按下方时长档位取值 |
| 夸张 | 强调时刻放大 | 空态、成功、错误等强调时刻可超出常规幅度；常规交互不夸张 |
| 立体造型 | 动效不破坏布局系统 | 只动 transform/opacity，不用 top/left/width/height 触发 layout |
| 吸引力 | 动效人格一致 | 全站沿用同一 easing 词表和时长档位；不逐页更换动效性格 |

## 时长与缓动基准

时长档位（默认值，原型数据或项目模式可覆盖）：

- 微反馈（hover/press/图标切换）：120–200ms，ease-out。
- 弹层（tooltip/menu/dialog 出入）：180–320ms，进入 ease-out、退出 ease-in。
- 大区域转场（抽屉、跨页、全屏）：300–500ms，ease-in-out。
- 持续循环（loading/呼吸）不适用出入场档位，必须提供 reduced-motion 暂停。

Figma easing 名称到 CSS 记录形式（`motion.json` 与数值探针统一使用右列）：

| Figma | CSS computed 形式 |
|---|---|
| LINEAR | `linear` |
| EASE_IN | `cubic-bezier(0.42, 0, 1, 1)` |
| EASE_OUT | `cubic-bezier(0, 0, 0.58, 1)` |
| EASE_IN_OUT | `cubic-bezier(0.42, 0, 0.58, 1)` |
| SPRING | 无 CSS 等价；记录 `{stiffness, damping, mass}` 参数并用项目动效库实现，不生成数值探针 |

## 可访问性

- 每个含位移的动效必须有 `prefers-reduced-motion: reduce` 下的替代（降级为 opacity 或瞬时切换），持续循环必须暂停。
- 视差与大 canvas 动画在 reduced 下直接关闭；替代方式记录在 `motion.json` 的 `reducedMotion` 字段，验收时对照复核。
