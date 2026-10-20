# Figma 工程工作流规范入口

| 问题 | 规范 |
| --- | --- |
| 两个命令的入参、工作目录、manifest 和验收判定 | [Figma 工作流契约](${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md) |
| 图片、合成素材、视频下载和转换 | [assets.md](${CLAUDE_PLUGIN_ROOT}/guides/figma/assets.md) |
| 平面化 Figma 的结构二次重建 | [reconstruction.md](${CLAUDE_PLUGIN_ROOT}/guides/figma/reconstruction.md) |

## 工作模式

从零还原先 `t-figma-assets` 再 `t-figma-impl`；素材未就绪时 impl 可先行（资产延后模式），交付前补跑 assets 并完成绑定。职责不互相吞并：assets 不改 UI，impl 负责整页。

Figma MCP 的 metadata、design context 和截图都是证据，不是生产 DOM。设计师按 Photoshop 式平面排版时，必须先按视觉边界、现有代码和项目规则做二次重建，再进入实现。

项目代码和已有组件优先于插件默认实现方式；设计视觉与项目 token 冲突时沿用项目 token，并在验收结论中记录取舍。
