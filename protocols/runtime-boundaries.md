# Runtime Boundaries

## Plugin-Owned Paths

以下路径属于插件自身，可作为稳定引用：

- `skills/`
- `agents/`
- `guides/`
- `protocols/`
- `.claude-plugin/`

## Target-Project Runtime Paths

以下路径属于目标项目仓库，不是插件自带资源：

- `AGENTS.md`
- `CLAUDE.md`
- `docs/`
- `.ai/`
- `scripts/`

规则：

- 若 `AGENTS.md` 与插件文档、guide、protocol 或既有产物冲突，显式报告冲突。
- 读取 `docs/`、`.ai/`、`scripts/` 时，把它们视为目标项目运行时产物。
- 目标项目根目录下的 `scripts/` 是环境启动、测试执行、Demo 运行等脚本的优先入口；插件 `scripts/` 仅作为未初始化或缺少本地脚本时的兼容回退。
- 项目本地脚本可以按项目需要调整 Docker 镜像、容器名、端口、环境变量和启动细节，但脚本文件名、主要命令行参数和输出契约应保持稳定。
- 项目事实、开发规范、质量门禁来自 `guides/`。
- 跨 skill 或 agent 的结构化字段、状态结构、报告格式优先来自 `protocols/`。
- `SKILL.md` 和 agent 文档只定义如何编排、何时读取、需要返回什么，不重写 guide/protocol 中已有规则。
