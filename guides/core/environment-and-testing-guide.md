# 环境与测试总览

本文档回答两个问题：

- 当前任务应该使用哪个环境？
- 当前需求应该写哪一层测试？

## 环境选择

| 任务 | 推荐入口 |
| --- | --- |
| 日常开发环境 | 手动启动 PostgreSQL + Redis + cargo run + npm run dev |
| 后端测试 | `uv run scripts/backend-test.py -- [filter]` |
| 前端类型检查与构建 | `cd frontend && npm run type-check` / `npm run build` |
| Demo / E2E | `uv run scripts/demo-test-runner.py demo/e2e/[test].ts` |

说明：

- 环境优先通过目标项目脚本管理；插件脚本是统一入口，具体端口和依赖以目标项目配置为准。
- Demo 环境与开发环境端口冲突，不能同时运行。
- AI 默认不主动启动开发环境，除非任务明确需要。

## 测试层级

| 需求类型 | 首选测试层级 |
| --- | --- |
| 完整用户故事、页面主链路、演示路径 | Demo / E2E |
| 前端局部逻辑、状态机、边界处理 | Frontend 测试 |
| API、后端业务流程、数据库交互 | Backend 测试 |

约束：

- 已由 Demo 覆盖的完整主链路，不再重复补同路径前端测试。
- 路由、租户前缀和 API base path 以目标项目当前设计与代码为准，不从历史示例推断。

## 入口

- Demo：[`e2e-testing.md`](${CLAUDE_PLUGIN_ROOT}/guides/demo/e2e-testing.md)
- Backend：[`testing.md`](${CLAUDE_PLUGIN_ROOT}/guides/backend/testing.md)
- Frontend：[`testing.md`](${CLAUDE_PLUGIN_ROOT}/guides/frontend/testing.md)
- 质量门禁：[`quality.md`](${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md)

## 可选 AI 工作流

`/t-tools:t-*` 工作流命令可作为辅助工程入口，但不是仓库默认构建/测试入口。优先遵循当前脚本、构建和测试命令。
