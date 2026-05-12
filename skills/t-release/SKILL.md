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

## 目标
- 更新项目中所有版本号文件。
- 编译验证版本号变更无误。
- 创建 git commit 和 tag，推送到远程。

## 参数
```bash
/t-release [版本号]
```

`版本号` 说明：
- 语义化版本号，如 `0.2.0`、`1.0.0`（不需要 `v` 前缀）
- 留空时：提示用户输入或选择版本号

## Preconditions
- 当前分支为 `main`。
- 工作区干净（无未提交变更）。
- 远程可访问。

## 版本文件清单
扫描并更新以下位置（存在则更新，不存在则跳过）：

| 文件 | 字段/行 | 说明 |
|---|---|---|
| `backend/Cargo.toml` | `[workspace.package]` 下的 `version` | Rust workspace 版本 |
| `frontend/package.json` | `"version"` | 前端版本（若无此字段则添加） |
| `demo/package.json` | `"version"` | Demo 测试版本 |

扫描规则：
- 用 Grep 搜索 `Cargo.toml` 和 `package.json` 中所有 `version` 字段。
- 仅更新项目自身的版本号，不修改依赖的版本号。
- `Cargo.lock` 不需要手动更新，`cargo check` 会自动处理。

## 执行流程

1. **前置检查**
   - `git status` 确认工作区干净。
   - `git tag --sort=-v:refname | head -5` 获取最新 tag 作为参考。
   - 读取当前各文件的版本号。

2. **确认版本号**
   - 若参数提供了版本号：直接使用。
   - 若未提供：根据当前最新 tag 推荐下一版本号（patch +1），并询问用户确认。

3. **更新版本号**
   - 使用 Edit 工具逐一更新各文件中的版本号。
   - 确保 `frontend/package.json` 存在 `version` 字段（缺失则在 `"name"` 后添加）。

4. **编译验证**
   ```bash
   cd backend && cargo check 2>&1
   ```
   - 编译失败则终止，不创建 commit。

5. **提交与打 Tag**
   ```bash
   git add backend/Cargo.toml backend/Cargo.lock frontend/package.json demo/package.json
   git commit -m "chore: bump version to <版本号>

   Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
   git tag v<版本号>
   ```

6. **推送**
   ```bash
   git push
   git push origin v<版本号>
   ```

7. **输出结果**
   - 显示更新了哪些文件。
   - 显示 commit hash 和 tag 名称。
   - 确认推送成功。

## 失败处理
- 工作区脏：提示用户先处理未提交变更，终止发布。
- 编译失败：终止，不创建 commit，保留已修改的版本文件供用户排查。
- 推送失败：commit 和 tag 已在本地，提示用户手动 `git push && git push origin v<版本号>`。
- tag 已存在：提示 tag 冲突，终止。

## Forbidden
- 在非 main 分支上执行发布。
- 跳过编译验证直接提交。
- 修改依赖版本号。
- 使用 `--force` 推送。
- 修改 `Cargo.lock` 中依赖版本。

## Examples

```bash
# 指定版本号发布
/t-release 0.2.0

# 交互式选择版本号
/t-release
```

期望响应：
```
版本已更新到 0.2.0，commit abc1234 和 tag v0.2.0 已推送到远程。

修改的文件：
- backend/Cargo.toml — 0.1.1 → 0.2.0
- backend/Cargo.lock — 自动更新
- frontend/package.json — 0.1.1 → 0.2.0
- demo/package.json — 0.1.1 → 0.2.0
```
