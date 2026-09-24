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
| Demo / E2E | `uv run scripts/web-demo-test-runner.py demo/e2e/[test].ts` |
| Extension Demo / E2E | `uv run scripts/web-demo-test-runner.py demo/e2e/extension/[test].e2e.ts [--no-auto-env]` |

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

新增测试先说明要防止的可观察回归。完整用户故事优先 Demo，后端跨模块/API/数据库行为优先场景测试；局部测试仅用于上述层级难以稳定覆盖的重要规则或边界。没有增量测试价值时不新增测试，仍定向运行受影响的现有测试并完成构建或类型检查。

约束：

- 已由 Demo 覆盖的完整主链路，不再重复补同路径前端测试。
- 路由、租户前缀和 API base path 以目标项目当前设计与代码为准，不从历史示例推断。

规划和交付时按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 记录验证责任与结果；没有新增测试不等于没有行为验证，编译或类型检查不能单独证明业务变更正确。

## 入口

- Demo：[`e2e-testing.md`](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/e2e-testing.md)
- Chrome 扩展演示：[`demo-testing.md`](${CLAUDE_PLUGIN_ROOT}/guides/extension/demo-testing.md)
- Backend：[`testing.md`](${CLAUDE_PLUGIN_ROOT}/guides/backend/testing.md)
- Frontend：[`testing.md`](${CLAUDE_PLUGIN_ROOT}/guides/frontend/testing.md)
- 质量门禁：[`quality.md`](${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md)

