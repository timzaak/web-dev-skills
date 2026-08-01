---
name: t-demo-run-all
description: Discover all non-live Demo E2E tests and run them one file at a time in the main session, diagnosing and fixing failures inline, restarting the environment after backend code changes and rebuilding demo data between files, until every file is resolved or exhausts its retry budget.
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
单文件运行与修复闭环统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/demo-run-repair-contract.md`

## 目标

- 自动发现除 `live/`、`fixtures/`、`templates/`、`verification/` 和文件名含 `test-` 之外的全部 Demo 测试。
- **由当前主会话逐个文件驱动**，每一步都是可观察、可中断的短 Bash / Agent 调用。
- 单文件失败时复用 `/t-demo-run` 的修复流程：整文件跑 → 失败时拆用例 → 每用例诊断 → 分发修复 → 补测 → 重跑，每文件最多 6 次尝试。
- 当次修复实际产生后端代码变动时，在当前 Demo 验证前重建环境。
- 文件之间重建 Demo 环境和数据容器，避免前一文件产生的业务数据影响后续测试。
- 每文件达到上限仍失败则标记 `FAILED` 并继续下一个文件，不阻塞整批。
- 持续写盘批次状态，支持 `continue` 从未完成文件的断点恢复。
- 产出 Markdown + JSON 汇总报告。

## 为什么不再 fork 嵌套 `claude -p`

旧版本对每个文件 spawn 一个嵌套 Claude CLI 子进程并串行等待，叠加多轮 diagnose→fix→retest 和长超时，会长时间阻塞发起调用的会话。本 skill 改为**主会话直接驱动循环**：每条命令都是独立、可见的 Bash/Agent 调用，可以随时 Ctrl-C 后用 `/t-demo-run-all continue` 从断点恢复。

## 使用方式

```bash
/t-demo-run-all            # 从头运行全部非 live 文件
```

```bash
/t-demo-run-all continue   # 从最近运行中批次的未完成断点继续
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

用短命令写入当前文件断点；不要在主会话读取、展开或覆盖整份 JSON：

```bash
uv run scripts/demo-run-all.py checkpoint --json <json_report> --index <zero_based_index>
```

#### B2. 运行整个测试文件

```bash
uv run scripts/demo-test-runner.py "<rel_path>" --run-id "<batch_run_id>-<file_key>-initial" --mode fast
```

`demo-test-runner.py` 会自检并按需启动/恢复 demo 环境（健康检查 + 必要时 `demo_env.start_environment`）。解析其**最后一行**：

```text
Result: {"success":"true|false","logs":"...","exitCode":0,"testFile":"...","runId":"..."}
```

按 `demo-run-repair-contract.md` 映射为 snake_case 批次 entry 字段。`file_key` 必须由相对路径的稳定 slug 或短哈希生成，避免不同目录的同名文件冲突。

#### B3. 整文件通过

`success == "true"`：本文件标记 `passed`、`fixed=false`，跳到 B5。

#### B4. 整文件失败 → 执行共享修复闭环

按 `demo-run-repair-contract.md` 处理当前失败用例，最多 6 轮。关键约束：

- 诊断必须使用实际失败 run ID；`--list-tests` 不得替换诊断证据。
- 以修复前后实际文件变化为准；当次修复产生后端代码变动时，在当前 Demo 验证前重建环境。
- 定向失败全部消除后必须运行整文件终验。终验通过才记 `status=passed, fixed=true`。
- 达到上限仍失败时记 `status=failed, fixed=false`，保留最后失败证据并继续批次。

#### B5. 持久化 + 文件间数据隔离

1. **保留最小结果**：只保留 `{status, exit_code, duration, run_id, logs, fixed}`；仅失败时再保留一句简短 `error`。文件名、下标、计数和总耗时由脚本推导。
2. **数据隔离**：若还有下一个文件，无论当前文件成功或失败，都先重建 Demo 环境和数据容器：
   ```bash
   uv run scripts/demo-stop.py --quiet && uv run scripts/demo-start.py
   ```
   - 重建失败：执行 `uv run scripts/demo-run-all.py block --json <json_report> --error "<简短原因>"` 后中止批次。该命令保留断点且不追加结果。
3. **写结果并推进断点**：数据隔离成功，或当前已是最后一个文件时，执行一条短命令：

   ```bash
   uv run scripts/demo-run-all.py record --json <json_report> --status <passed|failed> --exit-code <n> --duration <s> --run-id <id> --logs <path> [--fixed] [--error "<失败摘要>"]
   ```

   `record` 自动补齐 `test_file`，更新断点、计数和总耗时。成功结果不传 `--error`。

#### B6. 进入下一个文件

主会话进度只输出一行，不复述诊断、命令或 JSON：

```text
[<完成数>/<总数>] <PASS|FIXED|FAIL> <test_file> (<duration>s)
```

仅在 `FAIL` 或批次阻塞时追加一句原因；run ID、日志路径和累计统计留在最终报告中。

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

- `discover continue` 只恢复最近且 `batch_status=running` 的批次：存在 `current_file` 时从该文件重跑，否则从 `current_index`（必须等于已持久化 entry 数）继续。已持久化的成功或失败文件都不重跑。
- 无可继续内容（最近批次已完成、状态不一致或不存在）时脚本返回非零并提示，skill 终止。
- 恢复点总是某个尚未写最终 entry 的文件；从 B1 重跑该文件并重建当次修复上下文。

## 批次状态契约

`json_report` 由辅助脚本维护，主会话不得输出整份状态模板。恢复所需的最小语义为：

- `batch_status`: `running` | `completed`
- `discovered_files`: 仓库相对 posix 路径列表
- `entries[]`: 已完成文件的紧凑结果前缀
- `current_file`: 当前未完成文件；为空时从 `entries.length` 继续
- `last_error`: 仅阻塞时存在

计数、下标、总耗时和报告路径属于脚本派生/维护字段，不在主会话进度模板中重复生成。

## 汇总报告

由 `finalize` 子命令生成，必须包含：总文件数、通过数、修复数、失败数、通过率、总耗时，以及每个文件的状态/耗时/日志路径，外加 `Fixed Files` 与 `Unfixed Files` 清单。

## 失败处理

- 单文件达到 6 次仍失败：标记 `FAILED` 并继续下一个文件。
- `discover` 找不到文件或 `continue` 无可继续内容：终止并给出脚本返回的错误。
- 后端代码变动后的验证前重建失败：记录本轮失败，不在旧后端进程上验证。
- 文件间数据隔离失败：记入 `last_error` 并中断批次，由 `continue` 恢复。
- runner 启动失败：按整文件失败处理，记录错误并继续。

## 质量门禁

- **由主会话直接驱动循环；禁止 fork 嵌套 `claude -p` 或任何把整批吞进单一长阻塞 Bash 调用的写法。**
- 不允许并行执行多个测试文件。
- 不允许使用 slow/headed 模式。
- 每文件修复上限 6 次（diagnose→fix→补测→重跑）；超限标 `FAILED` 继续。
- 当次修复实际产生后端代码变动时，必须在当前 Demo 验证前重建环境；判定以修复前后文件变化为准，不以 agent 类型或 `change_scope` 代替。
- 进入下一文件前必须重建 Demo 数据环境；重建失败时不得继续。
- 所有 `Agent` 调用必须先按 `subagent-dispatch.md` 注入角色规范。
- 必须用 `checkpoint` / `record` 在每文件前后写盘状态，不得由主会话覆盖整份 JSON；必须以 `finalize` 收尾产出报告。
- 排除 `live/`、`fixtures/`、`templates/`、`verification/` 目录及文件名含 `test-` 的文件。
- 单文件修复闭环以 `demo-run-repair-contract.md` 为唯一契约源，本 skill 只编排批次状态、文件间隔离和汇总。
