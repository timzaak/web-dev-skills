# t-release / 版本发布

Bump project version, create git tag, and push release commit to remote.

更新项目版本号、创建 git commit 和 tag、推送到远程。

## Usage / 用法

```bash
/t-release [版本号]
```

- 语义化版本号，如 `0.2.0`、`1.0.0`（不需要 `v` 前缀）
- 留空时基于最新 tag 推荐下一版本号（patch +1）

## Preconditions / 前置条件

- 当前分支为 `main`
- 工作区干净（无未提交变更）
- 远程可访问

## Updated Files / 更新文件

| File / 文件 | Field / 字段 | Note / 说明 |
|---|---|---|
| `backend/Cargo.toml` | `version` under `[workspace.package]` | Rust workspace |
| `frontend/package.json` | `"version"` | Frontend |
| `demo/package.json` | `"version"` | Demo tests |

`Cargo.lock` is auto-updated by `cargo check`.

## Flow / 执行流程

1. 前置检查 — 确认工作区干净，读取当前版本号
2. 确认版本号 — 参数提供则直接使用，否则推荐并询问
3. 更新版本号 — 编辑各文件
4. 编译验证 — `cargo check`，失败则终止
5. 提交 & 打 Tag — `git commit` + `git tag v<版本号>`
6. 推送 — `git push` + `git push origin v<版本号>`

## Error Handling / 失败处理

- 工作区脏：提示用户先处理，终止发布
- 编译失败：终止，保留已修改文件供排查
- 推送失败：commit 和 tag 已在本地，提示手动推送
- tag 已存在：提示冲突，终止

## Examples / 示例

```bash
# 指定版本号
/t-release 0.2.0

# 交互式选择
/t-release
```

Expected output / 期望输出：

```
版本已更新到 0.2.0，commit abc1234 和 tag v0.2.0 已推送到远程。

修改的文件：
- backend/Cargo.toml — 0.1.1 → 0.2.0
- backend/Cargo.lock — 自动更新
- frontend/package.json — 0.1.1 → 0.2.0
- demo/package.json — 0.1.1 → 0.2.0
```
