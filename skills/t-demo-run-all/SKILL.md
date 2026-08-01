---
name: t-demo-run-all
description: Discover all non-live Demo E2E tests and run them one file at a time in the main session, diagnosing and fixing failures inline, restarting the demo environment after backend/frontend fixes, until every non-live file has passed, been fixed, or exhausted its retry budget.
argument-hint: "[continue]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Agent
---

# 批量运行 Demo 测试（主会话逐文件驱动）

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

## 目标

- 自动发现除 `live/`、`fixtures/`、`templates/`、`verification/` 和文件名含 `test-` 之外的全部 Demo 测试。
- **由当前主会话逐个文件驱动**，每一步都是可观察、可中断的短 Bash / Agent 调用。
- 单文件失败时复用 `/t-demo-run` 的修复流程：整文件跑 → 失败时拆用例 → 每用例诊断 → 分发修复 → 补测 → 重跑，每文件最多 6 次尝试。
- **修复触及 backend 或 frontend 源码时，在进入下一个文件前重启 demo 环境**，保证修复生效。
- 每文件达到上限仍失败则标记 `FAILED` 并继续下一个文件，不阻塞整批。
- 持续写盘批次状态，支持 `continue` 从中断/失败位置恢复。
- 产出 Markdown + JSON 汇总报告。

## 为什么不再 fork 嵌套 `claude -p`

旧版本对每个文件 spawn 一个 `claude --dangerously-skip-permissions -p "/t-demo-run <file>"` 子进程并串行等待，叠加每文件最多 6 轮 diagnose→fix→retest 与 7200 秒超时，会把发起该 Bash 调用的会话冻结数小时。本 skill 改为**主会话直接驱动循环**：每条命令都是独立、可见的 Bash/Agent 调用，可以随时 Ctrl-C 后用 `/t-demo-run-all continue` 从断点恢复。

## 使用方式

```bash
/t-demo-run-all            # 从头运行全部非 live 文件
```

```bash
/t-demo-run-all continue   # 从最近一次批次的 current_file 或最近失败文件继续
```

## 执行流程

### A. 发现阶段（一次性，脚本辅助）

```bash
uv run scripts/demo-run-all.py discover [--filter-file <path>]
```

`continue` 时改为：

```bash
uv run scripts/demo-run-all.py discover continue
```

发现规则（脚本内固化，不要在 skill 层重写）：
```bash
Glob: demo/e2e/**/*.e2e.ts
```
排除：路径任意一段为 `fixtures/`、`templates/`、`verification/`、`live/`，或文件名包含 `test-`。

该命令在 stdout 打印单行 JSON，**必须解析它**，字段：
- `discovered_files`: 仓库相对路径列表（posix）
- `batch_run_id`: 本次批次 ID（fresh 形如 `run-all-<ts>`，continue 为 JSON 文件名）
- `json_report` / `md_report`: 批次产物路径（仓库相对）
- `resume_index`: 本次应从 `discovered_files` 的第几个开始（fresh 为 0）
- `resumed_from`: continue 时的起始文件；fresh 为空字符串

脚本同时已写好初始批次 JSON（fresh）或已截断/重置好状态（continue）。若脚本返回非零，按其错误信息处理（如 `continue` 找不到可继续内容则终止）。

### B. 主循环：对 `discovered_files[resume_index:]` 逐个文件

设 `batch_run_id` 与脚本返回的 `json_report`（绝对路径 = `${目标项目根}/${json_report}`）已在手。对每个文件记其 `zero_based_index`（在 `discovered_files` 中的全量下标，不是切片下标）。

每个文件执行：

#### B1. 写断点

向 `json_report` 写入 `current_index = zero_based_index`、`current_file = <rel>`、`updated_at`，确保中断可恢复。每次写入后立即落盘（用 Write 工具覆盖整个 JSON）。

#### B2. 运行整个测试文件

```bash
uv run scripts/demo-test-runner.py "<rel_path>" --run-id "<batch_run_id>-<stem>" --mode fast
```

`demo-test-runner.py` 会自检并按需启动/恢复 demo 环境（健康检查 + 必要时 `demo_env.start_environment`）。解析其**最后一行**：

```text
Result: {"success":"true|false","logs":"...","exit_code":0,"testFile":"...","runId":"..."}
```

记录本次的 `run_id`（用命令传入的 `--run-id`）与 `logs`。

#### B3. 整文件通过

`success == "true"`：本文件标记 `passed`、`fixed=false`，跳到 B5。

#### B4. 整文件失败 → 修复循环（本文件最多 6 次）

进入修复循环前先初始化本文件聚合改动域 `agg_scope = {backend:false, frontend:false, miniapp:false, flutter:false, demo:false}`。

循环（最多 6 次）：

1. **列用例**（仅首次或用例集可能变化时）：
   ```bash
   uv run scripts/demo-test-runner.py "<rel_path>" --list-tests
   ```
2. 对每个失败用例（**串行**）：
   - **诊断**：按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 注入角色规范后调用 `Agent(subagent_type="demo-diagnose")`，传入 `testFile`、`runId`（= 本文件最后一次 run id）、`testCaseTitle`。诊断只读，输出 `.ai/diagnose/<简名>-<ts>.md`，给出 `recommended_agent`。
   - **修复**：读诊断的 `recommended_agent`，按 `subagent-dispatch.md` 注入角色规范后调用对应 dev agent：`Agent(subagent_type="demo-dev" | "frontend-dev" | "backend-dev" | "miniapp-dev" | "flutter-dev")`。
   - **读取返回契约**：解析 agent 返回的 `task_completion`（见 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md`），取 `change_scope` 与 `tests_to_run`。把 `change_scope` 各布尔 OR 进 `agg_scope`。
   - **补测**：按 `tests_to_run` 串行执行，层顺序固定 `backend -> frontend -> miniapp -> flutter -> demo`，命令必须命中 `${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md` 白名单。
     - miniapp 层仅在目标项目存在 `miniapp/` 或诊断归因到小程序时执行；flutter 层仅在存在声明 Flutter SDK 的 `pubspec.yaml` 或诊断归因到 Flutter 时执行；否则跳过。
     - agent 未返回 `tests_to_run`：记录契约缺失（P1），执行该改动层至少 1 条最小兜底补测。
     - 补测失败：记录风险，不阻断本用例的 demo 重跑与后续尝试。
   - **重跑当前用例**（即 `demo` 层验证）：
     ```bash
     uv run scripts/demo-test-runner.py "<rel_path>" --run-id "<batch_run_id>-<stem>-<attempt>" --grep "<用例标题>"
     ```
     更新本文件最近 `run_id` / `logs`。
3. 全部用例通过 → 本文件标记 `fixed=true`、`status=passed`，跳出循环到 B5。
4. 本轮仍有失败且未达 6 次 → 继续下一轮。
5. 达 6 次仍有失败 → 本文件标记 `status=failed`、`fixed=false`，记录最后一次 `run_id`/`logs`/`error`，跳出循环到 B5（**不阻塞批次，进入下一个文件**）。

#### B5. 持久化 + 重启决策（进入下一个文件前）

1. **写 entry**：把本文件的 `{test_file, status, exit_code, duration, run_id, logs, summary, error, fixed}` 追加进 `json_report` 的 `entries`；同步更新 `current_index = zero_based_index + 1`、`current_file = ""`、`passed_files`/`failed_files`、`total_duration`，落盘。
2. **环境重启决策**：仅当本文件 `fixed == true` **且** `agg_scope.backend == true 或 agg_scope.frontend == true` 时，重启 demo 环境（demo-env 只做健康检查，不会自动加载最新后端/前端代码，必须显式重启）：
   ```bash
   uv run scripts/demo-stop.py --quiet && uv run scripts/demo-start.py
   ```
   - 重启失败：在 entry 记 `env_restart_error`，**不中断批次**（下一个文件的 `demo-test-runner.py` 会再自检并尝试恢复健康）。
   - 仅 `demo`（`.e2e.ts`）/ `miniapp` / `flutter` 改动 → **不重启**（这些不依赖 demo 环境里常驻的 backend/frontend 进程）。

#### B6. 进入下一个文件

### C. 收尾

所有文件处理完（或切片耗尽）后：

```bash
uv run scripts/demo-run-all.py finalize --json <json_report>
```

脚本读取 `entries` 渲染 Markdown 报告、置 `batch_status=completed`、回写 JSON 与 MD，并在 stdout 打印 `Passed: N  Failed: M`。`failed_count == 0` 时返回 0，否则返回 1。

失败文件的诊断报告已在 B4 内联生成，**批次结束后不再单独批量跑 `demo-diagnose`**。

## 恢复机制

中断（手动 Ctrl-C、会话结束、上下文压缩）后：

```bash
/t-demo-run-all continue
```

- `discover continue` 读最近 `demo-run-all-*.json`：若存在 `current_file` 从该文件重跑；否则从最近一个 `failed` 文件重跑；已确认完成的文件不重跑。
- 无可继续内容（最近批次已完成或不存在）时脚本返回非零并提示，skill 终止。
- `agg_scope` 是内存态，恢复时丢失——这不影响正确性：恢复点总是某个尚未写最终 entry 的文件，会从 B1 重跑该文件，`agg_scope` 重新累加。

## 批次状态契约

`json_report` 必须持续写盘，至少包含（与脚本约定一致，旧报告向后兼容）：

- `batch_status`: `running` | `completed`
- `invocation`: `fresh` | `continue`
- `current_index`, `current_file`
- `discovered_files`: 仓库相对 posix 路径列表
- `entries[]`: 每文件 `{test_file, status, exit_code, duration, run_id, logs, summary, error, fixed}`
- `total_files`, `passed_files`, `failed_files`, `total_duration`
- `json_report`, `markdown_report`, `updated_at`

## 汇总报告

由 `finalize` 子命令生成，必须包含：总文件数、通过数、修复数、失败数、通过率、总耗时，以及每个文件的状态/耗时/日志路径，外加 `Fixed Files` 与 `Unfixed Files` 清单。

## 失败处理

- 单文件达到 6 次仍失败：标记 `FAILED` 并继续下一个文件。
- `discover` 找不到文件或 `continue` 无可继续内容：终止并给出脚本返回的错误。
- 环境重启失败：记 `env_restart_error`，不中断批次。
- runner 启动失败：按整文件失败处理，记录错误并继续。

## 质量门禁

- **由主会话直接驱动循环；禁止 fork 嵌套 `claude -p` 或任何把整批吞进单一长阻塞 Bash 调用的写法。**
- 不允许并行执行多个测试文件。
- 不允许使用 slow/headed 模式。
- 每文件修复上限 6 次（diagnose→fix→补测→重跑）；超限标 `FAILED` 继续。
- 修复触及 backend/frontend 时，**必须**在进入下一个文件前重启 demo 环境；仅 demo/miniapp/flutter 改动不重启。
- 所有 `Agent` 调用必须先按 `subagent-dispatch.md` 注入角色规范。
- 必须在每文件前后写盘批次状态；必须以 `finalize` 收尾产出报告。
- 排除 `live/`、`fixtures/`、`templates/`、`verification/` 目录及文件名含 `test-` 的文件。
- 复用 `/t-demo-run` 既定的整文件→拆用例→诊断→修复→补测→重跑流程与补测命令白名单（`tests-to-run-contract.md`），不要在本 skill 另起一套。
