---
name: t-web-demo-run-all
description: Discover all non-live Demo E2E tests and run them one file at a time in the main session, diagnosing and fixing failures inline, restarting the environment after backend code changes and rebuilding demo data between files, until every file is resolved or exhausts its retry budget. Supports an optional scan mode that pre-runs all files without repairing, clusters failures by shared root cause, and fixes each unique cluster once before re-verifying affected files.
argument-hint: "[continue|scan]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Agent
---

# 批量运行 Demo 测试（主会话逐文件驱动）

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（判断脚本入口或项目事实与插件默认冲突时读）
单文件运行与修复闭环：`${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md`（处理任一失败文件前读）

## 目标

- 自动发现除 `live/`、`fixtures/`、`templates/`、`verification/` 和文件名含 `test-` 之外的全部 Demo 测试。
- **由当前主会话逐个文件驱动**，每一步都是可观察、可中断的短 Bash / Agent 调用。
- 单文件失败时复用 `/t-tools:t-web-demo-run` 的修复流程：整文件跑 → 失败时拆用例 → 每用例诊断 → 分发修复 → 补测 → 重跑，每文件最多 6 次尝试。
- 文件之间重建 Demo 环境和数据容器，避免前一文件产生的业务数据影响后续测试。
- 每文件达到上限仍失败则标记 `FAILED` 并继续下一个文件，不阻塞整批。
- 持续写盘批次状态，支持 `continue` 从未完成文件的断点恢复。
- 产出 Markdown + JSON 汇总报告。

## 两种模式

默认逐文件模式（无参数 / `continue`）：发现 → 逐文件跑 → 失败就当场修复 → 文件间数据隔离 → 收尾。每个文件独立诊断修复，互不参照。

扫描模式（`scan`）：先纯 Bash 预跑全部文件**不修复**，按归一化错误指纹聚类失败，再对每个 unique cluster 只修一次（用 representative 文件），最后回扫所有受影响文件。

**何时用扫描模式**：失败密集且疑似共享根因（如一批文件都挂在同一个失效 selector 或同一个后端接口变更上）。先用 `${CLAUDE_PLUGIN_ROOT}/guides/web-demo/batch-token-profiling.md` 的决策树判断；孤立失败为主或文件数少（< 5）时用默认模式，扫描模式的聚类开销不划算。不确定时先跑默认模式一次，再用该指南读画像决定。

## 执行流程（默认逐文件模式）

### A. 发现阶段（一次性，脚本辅助）

```bash
uv run scripts/web-demo-run-all.py discover [--filter-file <path>]   # fresh
uv run scripts/web-demo-run-all.py discover continue                 # 断点恢复
```

发现规则（脚本内固化，不要在 skill 层重写）：`Glob demo/e2e/**/*.e2e.ts`，排除路径任意一段为 `fixtures/`、`templates/`、`verification/`、`live/` 或文件名包含 `test-` 的文件。

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
uv run scripts/web-demo-run-all.py checkpoint --json <json_report> --index <zero_based_index>
```

#### B2. 运行整个测试文件

```bash
uv run scripts/web-demo-test-runner.py "<rel_path>" --run-id "<batch_run_id>-<file_key>-initial" --mode fast
```

`web-demo-test-runner.py` 会自检并按需启动/恢复 demo 环境（健康检查 + 必要时 `demo_env.start_environment`）。解析其**最后一行**：

```text
Result: {"success":"true|false","logs":"...","exitCode":0,"testFile":"...","runId":"..."}
```

按 `web-demo-run-repair-contract.md` 映射为 snake_case 批次 entry 字段。`file_key` 必须由相对路径的稳定 slug 或短哈希生成，避免不同目录的同名文件冲突。

#### B3. 整文件通过

`success == "true"`：本文件标记 `passed`、`fixed=false`，跳到 B5。

#### B4. 整文件失败 → 执行共享修复闭环

按 `web-demo-run-repair-contract.md` 处理当前失败用例，最多 6 轮。关键约束：

- 诊断必须使用实际失败 run ID；`--list-tests` 不得替换诊断证据。
- 以修复前后实际文件变化为准；当次修复产生后端代码变动时，在当前 Demo 验证前重建环境。
- 定向失败全部消除后必须运行整文件终验。终验通过才记 `status=passed, fixed=true`。
- 达到上限仍失败时记 `status=failed, fixed=false`，保留最后失败证据并继续批次。

#### B5. 持久化 + 文件间数据隔离

1. **保留最小结果**：只保留 `{status, exit_code, duration, run_id, logs, fixed}`；仅失败时再保留一句简短 `error`。文件名、下标、计数和总耗时由脚本推导。
2. **数据隔离**：若还有下一个文件，无论当前文件成功或失败，都先重建 Demo 环境和数据容器；重建失败时执行 `block` 后中止批次（该命令保留断点且不追加结果）：
   ```bash
   uv run scripts/demo-stop.py --quiet && uv run scripts/demo-start.py
   uv run scripts/web-demo-run-all.py block --json <json_report> --error "<简短原因>"
   ```
3. **写结果并推进断点**：数据隔离成功，或当前已是最后一个文件时，执行一条短命令。`record` 自动补齐 `test_file`，更新断点、计数和总耗时；成功结果不传 `--error`：

   ```bash
   uv run scripts/web-demo-run-all.py record --json <json_report> --status <passed|failed> --exit-code <n> --duration <s> --run-id <id> --logs <path> [--fixed] [--error "<失败摘要>"]
   ```

#### B6. 进入下一个文件

主会话进度只输出一行，不复述诊断、命令或 JSON：

```text
[<完成数>/<总数>] <PASS|FIXED|FAIL> <test_file> (<duration>s)
```

仅在 `FAIL` 或批次阻塞时追加一句原因；run ID、日志路径和累计统计留在最终报告中。

### C. 收尾

所有文件处理完（或切片耗尽）后：

```bash
uv run scripts/web-demo-run-all.py finalize --json <json_report>
```

脚本读取 `entries` 渲染 Markdown 报告（总文件数、通过数、修复数、失败数、通过率、总耗时、每文件状态/耗时/日志路径、`Fixed Files` 与 `Unfixed Files` 清单），置 `batch_status=completed`，并在 stdout 打印 `Passed: N  Failed: M`。`failed_count == 0` 时返回 0，否则返回 1。

失败文件的诊断报告已在 B4 内联生成，**批次结束后不再单独批量跑 `web-demo-diagnose`**。

## 恢复机制

中断（手动 Ctrl-C、会话结束、上下文压缩）后：

```bash
/t-tools:t-web-demo-run-all continue
```

- `discover continue` 只恢复最近且 `batch_status=running` 的批次：存在 `current_file` 时从该文件重跑，否则从 `current_index`（必须等于已持久化 entry 数）继续。已持久化的成功或失败文件都不重跑。
- 无可继续内容（最近批次已完成、状态不一致或不存在）时脚本返回非零并提示，skill 终止。
- 恢复点总是某个尚未写最终 entry 的文件；从 B1 重跑该文件并重建当次修复上下文。

## 批次状态契约

批次 JSON 由 `web-demo-run-all.py` 维护（`batch_status` / `discovered_files` / `entries[]` / `current_file` / `last_error` 等派生字段见脚本实现）。主会话不得读取、展开或整份重写 JSON，只通过 `discover` / `checkpoint` / `record` / `block` / `finalize` 子命令推进状态。

## 执行流程（扫描模式）

扫描模式把"先看全貌、再按唯一根因修"作为前置阶段，复用同一份批次 JSON 的 `scan_results` 字段。`scan`/`cluster` 子命令在 `${CLAUDE_PLUGIN_ROOT}/scripts/web-demo-run-all.py` 中定义。

### S1. 发现阶段

同默认模式的 A 阶段（`discover [continue]`）。

### S2. 预扫描（纯 Bash 驱动，禁止 subagent）

```bash
uv run scripts/web-demo-run-all.py scan --json <json_report> [--scan-run-id <id>]
```

为每个 `discovered_files` 条目建一条 `pending` 记录。幂等：已存在 `scan_results` 且未 `--force` 时直接返回当前进度。

逐文件跑 fast 模式，**不进修复闭环**（runner 调用与结果登记同默认模式 B2 的参数映射，run-id 用 `<scan_run_id>-<file_key>-scan`）：

```bash
uv run scripts/web-demo-test-runner.py "<rel_path>" --run-id "<scan_run_id>-<file_key>-scan" --mode fast
uv run scripts/web-demo-run-all.py scan --json <json_report> --file <rel_path> --status <passed|failed> --exit-code <n> --duration <s> --run-id <id> --logs <path>
```

约束：此阶段禁止 dispatch subagent；文件间数据隔离同默认模式 B5；每文件只输出一行进度。

### S3. 聚类（纯 Python，无 subagent）

```bash
uv run scripts/web-demo-run-all.py cluster --json <json_report>
```

读取 `scan_results` 里所有 `failed` 条目，从各自 `run_id` 指向的 `demo/test-results/runs/<run_id>/playwright-output.log` 提取失败用例，按归一化错误指纹聚成 clusters。stdout 单行 JSON 含：`total_files` / `passed` / `failed` / `unique_clusters`、`clusters[]`（每项 `{fingerprint, representative_error, affected_files[], affected_cases[]}`，按受影响文件数降序）、`unclusterable[]`（缺 run_id / 日志丢失 / 无可解析失败的条目，**不得静默丢弃**，需逐条人工处理或回退默认模式单文件修）。

### S4. 逐 cluster 修复（此阶段才用 subagent）

对 `clusters[]` 按受影响文件数降序逐个处理：

1. **选 representative**：取该 cluster 的 `affected_files[0]` 与 `affected_cases[0]`。
2. **修复闭环**：按 `web-demo-run-repair-contract.md` 的单文件执行顺序处理 representative（诊断用 `web-demo-diagnose`、修复按 `recommended_agent` 选 agent、所有 `Agent` 调用先注入角色规范且同 cluster 同角色复用注入文本、后端代码变动则在验证前重建环境、representative 终验通过才视为该 cluster 修复完成；最多 6 轮，超限标该 cluster 失败并继续下一个 cluster）。
3. **回扫受影响文件**：representative 修复后，对该 cluster 所有 `affected_files` 重跑 fast 模式（复用 S2 的 runner + `scan --file` 登记，run_id 用 `<scan_run_id>-<file_key>-verify`）。全部通过则这些文件标 `passed, fixed=true`；仍有失败则该文件存在独立根因，回退默认模式对该文件单独走 `web-demo-run-repair-contract.md` 闭环。回扫同样遵守文件间数据隔离。

### S5. 收尾

同默认模式的 C 阶段（`finalize`）。失败 cluster 的诊断报告已在 S4 内联生成，批次结束后不再单独批量跑 `web-demo-diagnose`。

> `finalize` 读取 `entries[]`；扫描模式逐文件结果落在 `scan_results`。收尾前需把 `scan_results` 的最终状态映射为 `entries`，或直接以 `scan_results` 为准产出报告。两字段语义平行，不得相互覆盖。

## 质量门禁

- **由主会话直接驱动循环；禁止 fork 嵌套 `claude -p` 或任何把整批吞进单一长阻塞 Bash 调用的写法。**
- 不允许并行执行多个测试文件，不允许使用 slow/headed 模式。
- 所有 `Agent` 调用必须先按 `subagent-dispatch.md` 注入角色规范。
- 必须以 `finalize` 收尾产出报告；不得由主会话覆盖整份 JSON。
- 单文件修复闭环以 `web-demo-run-repair-contract.md` 为唯一契约源，本 skill 只编排批次状态、文件间隔离和汇总。

## 失败处理

- `discover` 找不到文件或 `continue` 无可继续内容：终止并给出脚本返回的错误。
- 后端代码变动后的验证前重建失败：记录本轮失败，不在旧后端进程上验证。
- 文件间数据隔离失败：记入 `last_error` 并中断批次，由 `continue` 恢复。
- runner 启动失败：按整文件失败处理，记录错误并继续。
