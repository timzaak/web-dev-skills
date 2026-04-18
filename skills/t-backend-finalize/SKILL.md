---
name: t-backend-finalize
context: fork
description: >
  后端验收后的统一收口命令。固定执行 /simplify、clippy 自动修复、格式化和全量后端测试，并在失败后默认从失败步骤恢复。
argument-hint: [任务名称]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Task
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - Write
  - Bash
---

# 后端收口执行

运行时边界统一参考：`protocols/runtime-boundaries.md`

## Purpose
- 读取 `.ai/task/[feature]/.state.json` 和 `backend/finalize.md`。
- 在 `backend-accept` 通过后执行统一收口：
  - `/simplify`
  - `cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features`
  - `cargo fmt --all`
  - `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`
  - OpenAPI 文档导出与前端 API 生成
- 若任一步失败，修复后默认从失败步骤恢复，不提供额外恢复参数。

## Args
| 参数 | 说明 |
|---|---|
| `[feature]` | 功能名 |

## Preconditions
- `.ai/task/[feature]/.state.json` 必须存在且可解析。
- `backend` 阶段必须已生成，且存在：
  - `backend/index.md`
  - `backend/accept.md`
  - `backend/accept/*.md`
  - `backend/finalize.md`
- `tasks.backend.accept.status` 必须为 `completed`。

## Fixed Flow
1. 读取 `backend/accept.md` manifest、`backend/accept/*.md` item handoff、`backend/finalize.md`、backend 改动范围和最小必要状态。
2. 确定 `/simplify` 作用范围：
   - 优先使用 `finalize.md` 中声明的 feature 相关 backend 改动文件
   - 若未显式声明，则回退到当前工作区 `backend/**` 改动集
3. 执行 `/simplify`，简化目标范围内代码。
4. 执行 `cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features`。
5. 执行 `cargo fmt --all`。
6. 执行全量 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`。
7. 导出 OpenAPI 文档并生成前端 API 客户端：
   - 执行 `cd backend && cargo run --bin backend-app -- --export-openapi ../frontend/api.json && cd ../`
   - 验证生成的 OpenAPI JSON（格式、路径占位符 camelCase）
   - 执行 `cd frontend && npm run generate-api && cd ../`
   - 验证生成的 TypeScript 文件
8. 若任一步出现问题，则修复并从失败步骤恢复。

## State Transition
1. 开始前写入：
   - `tasks.backend.finalize.status = running`
   - `tasks.backend.finalize.started_at = <timestamp>`
   - `phases.backend.status = awaiting_finalize`
2. 维护步骤级状态：
   - `tasks.backend.finalize.current_step`
   - `tasks.backend.finalize.steps.simplify|clippy|fmt|full_test|openapi_export|frontend_api_gen`
3. 某一步成功后，写入对应 step 为 `completed`。
4. 某一步失败后：
   - `tasks.backend.finalize.status = failed`
   - `tasks.backend.finalize.last_error = <summary>`
   - `tasks.backend.finalize.current_step = <failed_step>`
   - `phases.backend.status = failed`
5. 再次执行同一命令时：
   - 默认从 `current_step` 或最后失败步骤恢复
   - 若失败发生在 `full_test` 或之后，修复后至少重新执行 `clippy -> fmt -> full_test -> openapi_export -> frontend_api_gen`
6. 全部成功后：
   - `tasks.backend.finalize.status = completed`
   - `tasks.backend.finalize.completed_at = <timestamp>`
   - `phases.backend.status = completed`

## Success Criteria
- `/simplify` 已执行且没有遗留待处理冲突。
- `cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features` 执行完成，收口结束时无 warning。
- `cargo fmt --all` 已执行。
- `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py` 全量通过。
- OpenAPI 文档已成功导出到 `frontend/api.json`。
- 前端 API 客户端已成功生成（`frontend/api/*.ts`）。

## Failure
- `accept` 未完成：拒绝执行，并提示先完成 `/t-run [feature] --phase backend`。
- `finalize.md` 缺失：提示先重新生成 backend 任务。
- OpenAPI 导出失败：提示检查 `utoipa` 注解完整性，修复后从 `openapi_export` 步骤恢复。
- 前端 API 生成失败：提示检查 OpenAPI JSON 格式，修复后从 `frontend_api_gen` 步骤恢复。
- 状态写入失败：重试一次，失败则终止。
- 超过 3 轮自动修复仍未通过：标记 `failed` 并返回阻塞步骤。

## Examples
```bash
/t-backend-finalize realm-user-rbac
```

## 相关引用
- `skills/t-task/SKILL.md`
- `skills/t-run/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/backend/testing.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md`
