---
name: t-push
description: 由 AI 基于 git diff 总结提交内容，使用脚本运行受影响区域 CI，通过后 git commit && git push。
allowed-tools:
  - Bash
---

# Push with Local CI

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

## Fixed Flow

先由 AI 读取 `git status --short` 和必要的 `git diff`，识别本次变更涉及的源码文件。

在生成 commit message 和调用脚本前，AI 必须清理本次变更源码文件中的明显低价值注释。清理范围只限本次变更文件，不做全仓历史清理。

应删除的低价值注释包括：

- 仅对应 `.ai/design`、`.ai/task` 章节名、item 名、步骤名的注释。
- 复述函数名、变量名、类型名、文件名或目录职责的注释。
- 逐行解释显而易见语句的注释，例如“设置值”“调用接口”“返回结果”。
- 标记开发阶段、迁移步骤、临时分层、实现顺序，但对运行时代码没有帮助的注释。
- 与当前实现不再一致、语义空泛、只表达“这里处理逻辑”的注释。

必须保留的注释包括：

- 解释业务规则、领域不变量、权限/安全边界、兼容性原因、外部协议约束的注释。
- 解释复杂算法、非直观性能取舍、并发/事务/生命周期风险的注释。
- 有明确责任人的 TODO/FIXME，或指向具体缺陷、后续任务、版本约束的注释。
- 测试追溯、license、lint/coverage 指令、生成代码标记、公共 API 文档注释。

清理后重新查看必要的 `git diff`，确认 diff 中剩余注释有实际信息增量，再总结本次变更并生成简洁 commit message。commit message 必须来自 AI 对清理后实际变更的总结，不能由脚本根据目录名自动猜测。

然后为本次 `/t-push` 执行生成一个新的 session id（例如 `YYYYMMDD-HHMMSS` 或短 UUID）。同一次执行中，如果 CI 失败、AI 修复后需要重跑脚本，必须复用同一个 session id；新的 `/t-push` 执行必须生成新的 session id，避免被上一次执行的缓存影响。

使用脚本完成验证、提交和推送：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --ci-session "<本次 t-push session id>" --message "<AI 生成的 commit message>"
```

脚本负责：

- 检查 `git status --short`，无变更时停止。
- 读取 tracked、staged、unstaged 和 untracked 文件，检测 backend、frontend、demo 变更范围；若仓库根目录是 Maven backend 项目且不存在 `backend/` 分层，则将根目录项目改动视为 backend 变更。
- 为受影响区域并发运行本地 CI；同一区域内部保持顺序执行。
- 记录该 session 内每个区域通过 CI 时的 diff 指纹；同一次 push 流程中重跑脚本时，已通过且 diff 未变化的区域直接跳过，避免例如 backend 通过后因为修复 frontend 又重复跑 backend。新的 `/t-push` 执行必须使用新的 session，不复用上次结果。
- 使用 AI 传入的 `--message` 作为 commit message；执行提交时没有 `--message` 则停止。
- CI 全部通过后执行 `git add -A`、`git commit` 和 `git push`。

## CI Rules

- Backend 变更：执行项目已有 Java 编译、测试和 Maven 质量任务（优先 wrapper：`mvn test` 和 `mvn verify`；若 `pom.xml` 已配置格式化或静态检查插件，再按项目已有 goal 补充执行）。若静态检查报错，AI 应根据错误信息修复代码后重新运行脚本，直到通过。
- Frontend 变更：执行 `npm run lint`、`npm run format:check`、`npm run type-check`、`npm run test:run`；其中 `format:check` 和 `test:run` 不存在时跳过。
- Demo 变更：执行 `npm run lint` 和 `npm run type-check`。
- 无 backend/frontend/demo 变更时跳过本地 CI，直接进入 commit/push。

## Script Commands

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --ci-session "<session>" --message "<message>"
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --ci-session "<session>" --message "<message>" --force-checks
```

`--ci-session` 只用于同一次 `/t-push` 执行内的失败修复重试；每次新的 `/t-push` 都应使用新的 session id。

`--force-checks` 会忽略当前 session 记录的区域级通过缓存，强制重跑本次 diff 涉及的所有区域 CI。

## Failure

- 任一 CI 步骤失败：脚本停止，不执行 commit/push，并输出失败区域和步骤。
- 执行提交但没有传入 `--message`：脚本停止，提示先由 AI 基于 diff 生成 commit message。
- commit 失败：脚本停止，不执行 push。
- push 失败：脚本输出错误，并提示本地 commit 已保留。

## Success Criteria

- 受影响区域的 CI 检查全部通过，或无受影响区域而跳过。
- 代码已 commit 并 push 到远程。
