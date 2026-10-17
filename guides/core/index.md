# Core 规范入口

core 规范入口，存放跨项目领域 的总规范、测试总览与 skill 创作准则。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| 跨领域质量总原则、问题分级与证据要求 | [quality.md](${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md) |
| 环境准备、测试分层与各领域测试入口 | [environment-and-testing-guide.md](${CLAUDE_PLUGIN_ROOT}/guides/core/environment-and-testing-guide.md) |
| skill 的 description、渐进披露、结构与写作原则 | [skill-authoring.md](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-authoring.md) |
| skill 的前向行为测试、触发边界测试与迭代 | [skill-testing.md](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-testing.md) |

## 使用规则

- `quality.md` 是跨领域质量总纲，具体领域门禁继续下沉到各自目录。
- `environment-and-testing-guide.md` 负责测试分层导航，不替代目标项目自己的详细测试规则。
- `skill-authoring.md` 与 `skill-testing.md` 由 `t-skill` 的两种模式和 skill 交付 task 的 agent 上下文共用；插件仓库特有的落位、命名和路由同步规则不在本目录重复。
