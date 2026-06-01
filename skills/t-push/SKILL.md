---
name: t-push
description: 由 AI 基于 git diff 总结提交内容，使用脚本运行受影响区域 CI，通过后 git commit && git push。
allowed-tools:
  - Bash
---

# Push with Local CI

运行时边界统一参考：`protocols/runtime-boundaries.md`

## Fixed Flow

先由 AI 读取 `git status --short` 和必要的 `git diff`，总结本次变更并生成简洁 commit message。commit message 必须来自 AI 对实际变更的总结，不能由脚本根据目录名自动猜测。

然后使用脚本完成验证、提交和推送：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --message "<AI 生成的 commit message>"
```

脚本负责：

- 检查 `git status --short`，无变更时停止。
- 读取 tracked、staged、unstaged 和 untracked 文件，检测 backend、frontend、demo 变更范围。
- 为受影响区域并发运行本地 CI；同一区域内部保持顺序执行。
- 使用 AI 传入的 `--message` 作为 commit message；执行提交时没有 `--message` 则停止。
- CI 全部通过后执行 `git add -A`、`git commit` 和 `git push`。

## CI Rules

- Backend 变更：执行 `cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features -- -D warnings`，然后执行 `cargo fmt --all`。若 clippy 报错（有无法自动修复的 lint），AI 应根据错误信息修复代码后重新运行脚本，直到通过。
- Frontend 变更：执行 `npm run lint`、`npm run format:check`、`npm run type-check`、`npm run test:run`；其中 `format:check` 和 `test:run` 不存在时跳过。
- Demo 变更：执行 `npm run lint` 和 `npm run type-check`。
- 无 backend/frontend/demo 变更时跳过本地 CI，直接进入 commit/push。

## Useful Script Options

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --dry-run
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --checks-only
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --message "chore: update workflow docs"
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --message "chore: update workflow docs" --no-push
```

## Failure

- 任一 CI 步骤失败：脚本停止，不执行 commit/push，并输出失败区域和步骤。
- 执行提交但没有传入 `--message`：脚本停止，提示先由 AI 基于 diff 生成 commit message。
- commit 失败：脚本停止，不执行 push。
- push 失败：脚本输出错误，并提示本地 commit 已保留。

## Success Criteria

- 受影响区域的 CI 检查全部通过，或无受影响区域而跳过。
- 代码已 commit 并 push 到远程。
