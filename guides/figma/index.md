# Figma 工程工作流规范入口

| 问题 | 规范 |
| --- | --- |
| 四个命令的产物、关联、manifest、动效规格、规则记忆和验收门禁 | [Figma 工作流契约](${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md) |
| 图片、合成素材、视频下载和转换 | [assets.md](${CLAUDE_PLUGIN_ROOT}/guides/figma/assets.md) |
| 平面化 Figma 的结构二次重建 | [reconstruction.md](${CLAUDE_PLUGIN_ROOT}/guides/figma/reconstruction.md) |
| 动效交互的原则基准、时长缓动和缺口裁决 | [motion.md](${CLAUDE_PLUGIN_ROOT}/guides/figma/motion.md) |
| 调试经验的候选、凝练和长期记忆 | [rules.md](${CLAUDE_PLUGIN_ROOT}/guides/figma/rules.md) |
| computed style、局部截图和 delta 收敛 | [measurement.md](${CLAUDE_PLUGIN_ROOT}/guides/figma/measurement.md) |

## 工作模式

标准顺序是 `t-figma-assets -> t-figma-impl -> t-figma-ux（按需）-> t-figma-fix（按需）`。四个命令共享由目标文件关联的 session，但职责不互相吞并：assets 不改 UI，impl 负责整页，ux 只补动效交互，fix 只精修明确节点。

Figma MCP 的 metadata、design context 和截图都是证据，不是生产 DOM。设计师按 Photoshop 式平面排版时，必须先按视觉边界、现有代码和项目规则做二次重建，再进入实现。

项目代码和已有组件优先于插件默认实现方式；设计视觉与项目 token 冲突时沿用项目 token，并在 `conflicts.json` 留下机器可读证据。
