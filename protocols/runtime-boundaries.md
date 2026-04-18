# Runtime Boundaries

用于所有 `/t-*` skills 和 agents 的统一边界说明。

## Plugin-Owned Paths

以下路径属于插件自身，可作为稳定引用：

- `skills/`
- `agents/`
- `guides/`
- `protocols/`
- `scripts/`
- `.claude-plugin/`

## Target-Project Runtime Paths

以下路径属于目标项目仓库，不是插件自带资源：

- `docs/`
- `.ai/`

规则：

- 读取 `docs/`、`.ai/` 时，把它们视为目标项目运行时产物。
- 项目事实、开发规范、质量门禁优先来自 `guides/`。
- 跨 skill 或 agent 的结构化字段、状态结构、报告格式优先来自 `protocols/`。
- `SKILL.md` 和 agent 文档只定义如何编排、何时读取、需要返回什么，不重写 guide/protocol 中已有规则。
