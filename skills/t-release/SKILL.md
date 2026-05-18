---
name: t-release
description: Bump project version, create git tag, and push release commit to remote.
argument-hint: [版本号]
allowed-tools:
  - Read
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
---

# 版本发布

## 用法
```bash
/t-release [版本号]
```

发布项目版本，更新版本文件，验证后创建 release commit 和 git tag，并推送到远程。

版本号使用语义化版本，如 `0.2.0`、`1.0.0`。版本文件写入纯版本号 `X.Y.Z`，最终 git tag 必须使用 `vX.Y.Z` 格式。用户输入 `0.2.0` 或 `v0.2.0` 时，都按版本号 `0.2.0` 发布，并创建 tag `v0.2.0`。

## 执行流程

使用发布脚本，不要手工拼接 release 命令：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/release.py [版本号]
```

如果用户未提供版本号，先运行脚本获取推荐版本：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/release.py
```

用户确认后，再用推荐版本执行：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/release.py <推荐版本号>
```

脚本负责：
- 检查 `main` 分支、干净工作区、远程可访问、tag 不冲突。
- 识别历史 `X.Y.Z` 和 `vX.Y.Z` tag，但新 tag 一律使用 `vX.Y.Z`。
- 更新 `backend/Cargo.toml`、`frontend/package.json`、`demo/package.json` 中存在的版本文件。
- 运行验证，创建 commit `chore: bump version to <版本号>`，创建并推送 tag `v<版本号>`。

## 失败处理
- 按脚本错误输出处理。
- 验证失败时终止，不创建 commit/tag。
- 推送失败时提示用户本地 commit/tag 状态和手动推送命令。

## Forbidden
- 绕过 `${CLAUDE_PLUGIN_ROOT}/scripts/release.py` 手工执行发布。
- 创建或推送不带 `v` 前缀的 release tag。
- 使用 `--force` 推送。
