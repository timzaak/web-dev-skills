# 环境与测试总览

本文档回答两个问题：

- 当前任务应该使用哪个环境？
- 当前需求应该写哪一层测试？

## 环境选择

| 任务 | 推荐入口 |
| --- | --- |
| 日常开发环境 | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/dev-start.py` |
| 后端测试 | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py` |
| 前端类型检查与构建 | `cd frontend && npm run type-check` / `npm run build` |
| Demo / E2E | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py demo/e2e/[test].ts` |

说明：

- 环境统一通过项目脚本管理。
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
- 单租户路径是当前默认事实，Demo 和前端测试不再使用租户前缀。

## 入口

- Demo：[`e2e-testing.md`](${CLAUDE_PLUGIN_ROOT}/guides/demo/e2e-testing.md)
- Backend：[`testing.md`](${CLAUDE_PLUGIN_ROOT}/guides/backend/testing.md)
- Frontend：[`testing.md`](${CLAUDE_PLUGIN_ROOT}/guides/frontend/testing.md)
- 质量门禁：[`quality.md`](${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md)

## 可选 AI 工作流

`/t-tools:t-*` 工作流命令可作为辅助工程入口，但不是仓库默认构建/测试入口。优先遵循当前脚本、构建和测试命令。
