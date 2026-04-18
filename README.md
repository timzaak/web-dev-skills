# T-Tools

面向 Rust + React 项目的 Claude Code plugin。它把 `PRD -> 设计 -> 任务 -> 实施 -> 验收 -> Demo` 串成一组 `/t-*` 命令，并用专职 sub-agent 执行各阶段工作。

## 工作流

```text
/t-prd -> /t-design -> /t-task -> /t-run -> /t-backend-finalize
                |            |          |
                v            v          v
      /t-design-check  /t-task-check  /t-demo-run
```

补充命令：
- `/t-prd-check`
- `/t-consistency-check`
- `/t-demo-run-all`
- `/t-demo-accept`

## 仓库职责

这是插件源码仓库，不是目标业务仓库。

- 插件自带资源：`skills/`、`agents/`、`guides/`、`protocols/`、`scripts/`
- 插件清单：`.claude-plugin/plugin.json`
- 目标项目运行时依赖：`docs/`、`.ai/`

引用插件内部文件时统一使用 `${CLAUDE_PLUGIN_ROOT}` 语义路径。`README` 只做入口说明；详细规则以下列目录中的文档为准。

## 目录分工

- `skills/`：命令入口、编排流程、输入输出契约
- `agents/`：角色职责、读取顺序、输出要求
- `guides/`：开发事实、质量门禁、操作指南
- `protocols/`：跨 skill/agent 的共享结构契约，避免在 `SKILL.md` / agent 中重复定义
- `scripts/`：统一脚本入口

新增的共享协议入口：

- `protocols/runtime-boundaries.md`：插件资源与目标项目运行时边界
- `protocols/task-state-contract.md`：`.state.json` 唯一结构真相
- `protocols/task-phase-execution.md`：phase/slot/item 编排规则
- `protocols/backend-test-execution.md`：backend-test 默认收敛与升级策略
- `protocols/design-check-rubric.md`：设计检查评分标准
- `protocols/prd-check-rubric.md`：PRD / user story 检查评分标准
- `protocols/task-check-rubric.md`：任务检查评分与阻塞规则
- `protocols/agent-task-output-contract.md`：实现类 agent 的通用结构化输出

## 快速使用

```bash
/t-tools:t-prd create user-management
/t-tools:t-design user-management
/t-tools:t-task user-management
/t-tools:t-run user-management --phase backend
```

## 关键入口

- 后端开发与门禁：[guides/backend/index.md](/guides/backend/index.md)
- 前端开发与门禁：[guides/frontend/index.md](/guides/frontend/index.md)
- Demo 测试与诊断：[guides/demo/index.md](/guides/demo/index.md)
- 产品文档规范：[guides/product/index.md](/guides/product/index.md)
- 跨领域总纲：[guides/core/index.md](/guides/core/index.md)
- 跨组件契约：[protocols/index.md](/protocols/index.md)

## 依赖

- Context7：供 `backend-dev`、`backend-test`、`frontend-dev`、`frontend-test` 查询第三方库文档
- `/simplify`：可选，用于 `t-backend-finalize` 收口审查
