---
name: t-push
description: 使用脚本根据 git diff 检测变更范围，运行受影响区域 CI，通过后 git commit && git push。
disable-model-invocation: true
allowed-tools:
  - Bash
---

# Push with Local CI

运行时边界统一参考：`protocols/runtime-boundaries.md`

## Fixed Flow

使用脚本，不要在 skill 中手工拼接范围检测、CI、commit 或 push 命令：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py
```

脚本负责：

- 检查 `git status --short`，无变更时停止。
- 读取 tracked、staged、unstaged 和 untracked 文件，检测 backend、frontend、demo 变更范围。
- 为受影响区域并发运行本地 CI；同一区域内部保持顺序执行。
- 生成简洁 commit message，或在显式传入 `--message` 时使用指定 message。
- CI 全部通过后执行 `git add -A`、`git commit` 和 `git push`。

## CI Rules

- Backend 变更：执行 `cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features`，然后执行 `cargo fmt --all`。
- Frontend 变更：执行 `npm run lint`、`npm run format:check`、`npm run type-check`、`npm run test:run`；其中 `format:check` 和 `test:run` 不存在时跳过。
- Demo 变更：执行 `npm run lint` 和 `npm run type-check`。
- 无 backend/frontend/demo 变更时跳过本地 CI，直接进入 commit/push。

## Useful Script Options

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --dry-run
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --checks-only
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --message "chore: update workflow docs"
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --no-push
```

## Failure

- 任一 CI 步骤失败：脚本停止，不执行 commit/push，并输出失败区域和步骤。
- commit 失败：脚本停止，不执行 push。
- push 失败：脚本输出错误，并提示本地 commit 已保留。

## Forbidden

- 绕过 `${CLAUDE_PLUGIN_ROOT}/scripts/push.py` 手工执行 `git add`、`git commit` 或 `git push`。
- CI 失败后继续 commit/push。
- 使用 `--force` 推送。

## Success Criteria

- 受影响区域的 CI 检查全部通过，或无受影响区域而跳过。
- 代码已 commit 并 push 到远程。
