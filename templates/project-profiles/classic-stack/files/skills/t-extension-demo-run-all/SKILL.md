---
name: t-extension-demo-run-all
description: 批量运行并修复 Chrome 扩展 Playwright 用户故事演示，维护独立批次报告和断点；普通 Web 批次使用 t-web-demo-run-all。
argument-hint: "[continue]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Agent
  - Task
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
---

# Extension Demo 批量运行

先读 `${CLAUDE_PLUGIN_ROOT}/guides/extension/demo-testing.md`、`${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md` 和 `${CLAUDE_PLUGIN_ROOT}/skills/t-web-demo-run-all/SKILL.md` 的批次状态命令。批次编排复用 `web-demo-run-all.py`，但始终传 `discover --scope extension --report-prefix extension-demo-run-all`；恢复时传 `discover continue --scope extension --report-prefix extension-demo-run-all`。只发现 `demo/e2e/extension/**/*.e2e.ts`，不可用 Web 默认批次混跑。

按发现顺序串行 checkpoint、运行与 record；单文件遵循 `/t-tools:t-extension-demo-run` 的诊断、最多六轮修复、补测和整文件终验。runner 仍用 `web-demo-test-runner.py`，每次运行使用唯一 run ID，fixture 独立管理环境时全程保留 `--no-auto-env`。文件间由 fixture 关闭 profile 和重置 stub；真实后端依赖按共享契约重建。失败文件记录证据后继续，环境恢复失败则调用 `block` 留下断点。全部文件处理完用 `finalize` 生成 `.ai/quality/extension-demo-run-all-*.json/.md`；只有零失败才报告批次通过。

批次 JSON 仅由脚本的 `discover/checkpoint/record/block/finalize` 更新，主会话不得整份重写；`continue` 从第一个未完成文件恢复，不覆盖已有日志。扫描聚类模式需要时沿用 Web 批次 skill 中同名子命令，但诊断与修复角色始终为 extension-demo 角色。
