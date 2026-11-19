# pi 规范入口

pi coding agent 二次开发规范入口，覆盖 TypeScript extension、随包分发的 Agent Skills / prompt template 与 pi package。按“先定位问题，再读对应页面”使用。技术基线为 Node.js 22.19+ / TypeScript / typebox，pi 通过 jiti 直接加载 TS，没有独立构建层。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| 新建 pi extension 包或为当前项目补齐开发设施 | [t-init --pi 初始化流程](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/pi-init.md)；入口为 `/t-init --pi <project-name>` 或 `/t-init --pi .` |
| 项目识别、首次交付、pi phase 适用性、push/release 门禁选择 | [pi-project-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/pi-project-contract.md) |
| 包布局与清单、扩展工厂与生命周期、工具/命令/事件/状态/UI 规则、provider 与 MCP、权限、打包分发 | [development.md](${CLAUDE_PLUGIN_ROOT}/guides/pi/development.md) |
| Vitest 边界、运行时冒烟证据与 `/reload` 开发循环 | [testing.md](${CLAUDE_PLUGIN_ROOT}/guides/pi/testing.md) |
| 完成前最小验证命令与门禁 | [validation.md](${CLAUDE_PLUGIN_ROOT}/guides/pi/validation.md) |
| 只读验收、截断/并发/生命周期/模式守卫检查 | [quality.md](${CLAUDE_PLUGIN_ROOT}/guides/pi/quality.md) |
| 编写随包分发的 skill | [skill-authoring.md](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-authoring.md) 与 [skill-testing.md](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-testing.md)；pi 特有差异见 development.md「Skills 与 prompt templates」 |

## 使用规则

- `development.md` 维护 pi 工程基线与事实型规则；项目 `package.json`、settings 与现有扩展是当前实现事实，跨阶段输出和验收判定由 protocols 定义。
- 与 frontend/extension 共享的 TypeScript 测试原则以 `guides/frontend/testing.md` 为准，本目录只维护 pi 特有差异。
- `testing.md` 只负责测试 how-to，不重述架构。
- agent 文档只定义执行顺序、门禁和输出契约，不重新发明 pi 的扩展 API 或契约规范。
