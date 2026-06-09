---
name: t-backend-finalize
description: Run backend finalization after backend acceptance by simplifying code, running Java quality tasks, exporting OpenAPI, and generating the frontend API client. Use when the user runs /t-backend-finalize with a feature name after backend acceptance is completed.
---

# 后端收口执行

运行时边界统一参考：`protocols/runtime-boundaries.md`

## Purpose
- 读取 `.ai/task/[feature]/.state.json` 和 `backend/finalize.md`。
- 在 `backend-accept` 通过后执行统一收口：
  - `/code-review`
  - Java 编译、测试和项目已有 Maven 质量任务
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
- 读取 `backend/accept.md` manifest、`backend/accept/*.md` item handoff、`backend/finalize.md`、backend 改动范围和最小必要状态。
- 确定 `/code-review` 作用范围：
   - 优先使用 `finalize.md` 中声明的 feature 相关 backend 改动文件
   - 若未显式声明，则回退到当前工作区 `backend/**` 改动集
- 执行 `/code-review`，简化目标范围内代码。
- 执行 Java 编译、测试和项目已有质量任务：
   - Maven 项目优先使用 `mvn test` 和 `mvn verify`。
   - 若 `pom.xml` 已配置格式化或静态检查插件，按项目已有 Maven goal 升级执行；本插件不要求新增这些依赖。
   - 不使用非 Java 后端工具链命令作为后端质量检查。
- 导出 OpenAPI 文档并生成前端 API 客户端：
   - 先根据目标仓库的 Spring Boot 启动方式、现有导出脚本或文档定位实际导出命令
   - 优先复用项目已有 OpenAPI 导出脚本；否则启动后端并请求 `/v3/api-docs` 写入 `frontend/api.json`
   - 验证生成的 OpenAPI JSON（格式、路径占位符、schema/tag）
   - 执行 `cd frontend && npm run generate-api && cd ../`
   - 验证生成的 TypeScript 文件
- 若任一步出现问题，则修复并从失败步骤恢复。

## State Transition
- 开始前写入：
   - `tasks.backend.finalize.status = running`
   - `tasks.backend.finalize.started_at = <timestamp>`
   - `phases.backend.status = awaiting_finalize`
- 维护步骤级状态：
   - `tasks.backend.finalize.current_step`
   - `tasks.backend.finalize.steps.code_review|java_quality|openapi_export|frontend_api_gen`
- 某一步成功后，写入对应 step 为 `completed`。
- 某一步失败后：
   - `tasks.backend.finalize.status = failed`
   - `tasks.backend.finalize.last_error = <summary>`
   - `tasks.backend.finalize.current_step = <failed_step>`
   - `phases.backend.status = failed`
- 再次执行同一命令时：
   - 默认从 `current_step` 或最后失败步骤恢复
   - 若失败发生在 `openapi_export` 或之后，修复后至少重新执行 `java_quality -> openapi_export -> frontend_api_gen`
- 全部成功后：
   - `tasks.backend.finalize.status = completed`
   - `tasks.backend.finalize.completed_at = <timestamp>`
   - `phases.backend.status = completed`

## Success Criteria
- `/code-review` 已执行且没有遗留待处理冲突。
- Java 编译、测试和项目已有质量任务已执行，收口结束时无阻塞问题。
- OpenAPI 文档已成功导出到 `frontend/api.json`。
- 前端 API 客户端已成功生成（`frontend/api/*.ts`）。

## Failure
- `accept` 未完成：拒绝执行，并提示先完成 `/t-run [feature] --phase backend`。
- `finalize.md` 缺失：提示先重新生成 backend 任务。
- OpenAPI 导出失败：提示检查 springdoc/OpenAPI 注解、Controller 声明和运行时启动问题，修复后从 `openapi_export` 步骤恢复。
- 前端 API 生成失败：提示检查 OpenAPI JSON 格式，修复后从 `frontend_api_gen` 步骤恢复。
- 状态写入失败：重试一次，失败则终止。
- 超过 3 轮自动修复仍未通过：标记 `failed` 并返回阻塞步骤。

## Examples
```bash
/t-backend-finalize <feature>
```

## 相关引用
- `skills/t-task/SKILL.md`
- `skills/t-run/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md`
