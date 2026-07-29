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

然后为本次 `/t-push` 执行生成一个新的 session id（例如 `YYYYMMDD-HHMMSS` 或短 UUID）。同一次执行中，如果 CI 失败、AI 修复后需要重跑脚本，必须复用同一个 session id；新的 `/t-push` 执行必须生成新的 session id，避免被上一次执行的缓存影响。

使用脚本完成验证、提交和推送：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --ci-session "<本次 t-push session id>" --message "<AI 生成的 commit message>"
```

脚本负责：

- 检查 `git status --short`，无变更时停止。
- 读取 tracked、staged、unstaged 和 untracked 文件，检测 backend、frontend、demo 变更范围。
- 为受影响区域并发运行本地 CI；同一区域内部保持顺序执行。
- 记录该 session 内每个区域通过 CI 时的 diff 指纹；同一次 push 流程中重跑脚本时，已通过且 diff 未变化的区域直接跳过，避免例如 backend 通过后因为修复 frontend 又重复跑 backend。新的 `/t-push` 执行必须使用新的 session，不复用上次结果。
- 使用 AI 传入的 `--message` 作为 commit message；执行提交时没有 `--message` 则停止。
- CI 全部通过后执行 `git add -A`、`git commit` 和 `git push`。

## CI Rules

- Backend 变更：依次执行 `cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features -- -D warnings`、`cargo fmt --all`，再执行一次不带 `--fix` 的 `cargo clippy --all-targets --all-features -- -D warnings` 作为最终校验（`--fix` 遇到无法自动修复的 denied lint 时仍会以 0 退出，仅靠 `--fix` 无法拦截，需此步骤才能真正强制 `-D warnings`）。若该校验报错，AI 应根据错误信息修复代码后重新运行脚本，直到通过。
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
