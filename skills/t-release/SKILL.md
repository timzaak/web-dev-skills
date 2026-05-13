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

`版本号` 使用语义化版本，如 `0.2.0`、`1.0.0`，不带 `v`。留空时基于最新 tag 推荐 patch +1，并让用户确认。

## Preconditions
- 当前分支为 `main`。
- 工作区干净（无未提交变更）。
- 远程可访问。
- 目标 tag 不存在。

## 更新范围

| 文件 | 字段/行 | 说明 |
|---|---|---|
| `backend/Cargo.toml` | `[workspace.package]` 下的 `version` | Rust workspace 版本 |
| `frontend/package.json` | `"version"` | 前端版本（若无此字段则添加） |
| `demo/package.json` | `"version"` | Demo 测试版本 |

只更新项目自身版本号，不修改依赖版本号。`Cargo.lock` 由验证命令按需自动更新。

## 执行流程

1. 检查分支、工作区、远程和 tag 冲突。
2. 确认目标版本号，读取当前版本号。
3. 更新存在的版本文件；缺失的目标文件跳过。
4. 运行项目验证：优先复用 `.github/workflows/ci.yml` 中的检查命令；没有 CI 配置时执行合理的 lint/type-check/fmt/clippy fallback。
5. 验证通过后提交并打 tag：
   - commit: `chore: bump version to <版本号>`
   - tag: `<版本号>`
6. 推送 commit 和 tag。
7. 输出更新文件、commit hash、tag 和推送结果。

## 失败处理
- 工作区脏：提示用户先处理未提交变更，终止发布。
- 编译失败：终止，不创建 commit，保留已修改的版本文件供用户排查。
- 推送失败：commit 和 tag 已在本地，提示用户手动推送。
- tag 已存在：提示 tag 冲突，终止。

## Forbidden
- 在非 main 分支上执行发布。
- 跳过编译验证直接提交。
- 修改依赖版本号。
- 使用 `--force` 推送。
