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

在生成 commit message 和调用脚本前，AI 必须清理本次变更源码文件中的违规注释：低价值注释定义、临时工作流文档（`.ai/design`、`.ai/task`）引用禁令和必须保留的注释类型均以 `${CLAUDE_PLUGIN_ROOT}/protocols/code-comment-contract.md` 为准。清理范围只限本次变更文件，不做全仓历史清理。

清理后重新查看必要的 `git diff`，确认 diff 中剩余注释有实际信息增量，再总结本次变更并生成简洁 commit message。commit message 必须来自 AI 对清理后实际变更的总结，不能由脚本根据目录名自动猜测。

然后为本次 `/t-push` 执行生成一个新的 session id（例如 `YYYYMMDD-HHMMSS` 或短 UUID），并调用脚本：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --ci-session "<本次 t-push session id>" --message "<AI 生成的 commit message>"
```

session 规则只说一次：同一次 `/t-push` 执行内（含 CI 失败后 AI 修复重跑）复用同一 session id；新的 `/t-push` 执行必须生成新 session id，避免复用上一次的区域通过缓存。

脚本负责：检测 backend/frontend/demo 变更范围并为受影响区域并发运行本地 CI（区域 CI 内容见下节）；按 session 记录每个区域通过 CI 时的 diff 指纹，重跑时已通过且 diff 未变的区域直接跳过；CI 全部通过后执行 `git add -A`、`git commit` 和 `git push`。无变更或缺少 `--message` 时脚本自行停止。

## CI Rules

- Backend 变更：`cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features -- -D warnings`、`cargo fmt --all`，再以不带 `--fix` 的 `cargo clippy --all-targets --all-features -- -D warnings` 终验。
- Frontend 变更：`npm run lint`、`npm run format:check`（不存在时跳过）、`npm run type-check`。
- Demo 变更：`npm run lint` 和 `npm run type-check`。
- 无 backend/frontend/demo 变更时跳过本地 CI，直接进入 commit/push。

`--force-checks` 参数可忽略 session 缓存，强制重跑本次 diff 涉及的所有区域 CI。

## Failure

- 任一 CI 步骤失败：脚本停止且不 commit/push，并输出失败区域和步骤；AI 根据错误信息修复代码后，用同一 session id 重新运行脚本，直到通过。
- commit/push 失败：脚本停止并报告错误；push 失败时本地 commit 已保留。
