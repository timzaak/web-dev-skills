# Demo Run Repair Contract

本协议是 `t-web-demo-run`、`t-web-demo-run-all` 共享的单文件 Playwright Demo E2E 运行、诊断、修复和回归契约。批次发现、断点和汇总由批次 skill 自行编排。

共享结果字段以 `${CLAUDE_PLUGIN_ROOT}/protocols/demo-result-contract.md` 为准；本协议只补充 Playwright runner 的映射和修复行为。

## Runner 输出适配

`${CLAUDE_PLUGIN_ROOT}/scripts/web-demo-test-runner.py` 最后一行输出：

```text
Result: {"success":"true|false","fixed":"false","logs":"...","exitCode":0,"testFile":"...","runId":"...","duration":1.2,"error":""}
```

编排层解析后统一映射为：

- `exitCode` -> `exit_code`
- `testFile` -> `test_file`
- `runId` -> `run_id`
- runner 返回的 `logs` 相对于 `demo/`；写入 skill 结果或批次 entry 前必须规范化为仓库相对路径 `demo/<logs>`
- `success` 仍按字符串 `"true" | "false"` 解析

若 runner 非零退出且没有合法的 `Result` 行，视为本次 Demo 验证失败，保留退出码和输出尾部作为 `error`。

## 单文件执行顺序

首次执行及恢复先读 scripts/index.md、任务 Validation 和 fixture，确认项目 URL、身份入口、环境管理与清理方式。项目本地 hook 管理环境，或使用 --no-auto-env 由 fixture/外部环境管理；模式必须持久化，scan/continue 不得静默改用其他环境。

1. 以 `fast` 模式运行整个测试文件。
2. 整文件通过时直接返回，`fixed=false`。
3. 失败时从该 run 的 `playwright-output.log` 提取失败用例标题；需要规范化完整标题时可执行 `--list-tests`。`--list-tests` 不得删除或覆盖失败 run 的日志。
4. 对失败用例串行执行诊断、修复、补测和定向 Demo 验证。
5. 定向失败全部消除后，必须再运行一次整个文件，防止修复导致其他用例回归。只有该次整文件通过才可返回 `status=passed, fixed=true`。

单文件最多进行 6 轮“诊断 -> 修复 -> 补测 -> 定向验证”。每轮只处理当前仍失败的用例，已通过用例不重复修复。整文件终验失败时，将新失败用例并入下一轮。

## 诊断、修复与补测

- 诊断使用 web-demo-diagnose，输入 testFile、实际失败的 runId 和 testCaseTitle。
- recommended_agent 为 web-demo-dev（测试资产）、project-dev（生产实现）或 manual（环境/权限）。
- 所有 Agent 调用必须先按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 注入角色规范。
- 修复返回必须按 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md` 解析 `task_completion.change_scope` 和 `tests_to_run`。
- 补测命令必须符合 `${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md`，并按 implementation -> web-demo 串行。与当前定向 Demo 验证完全相同的命令去重，不重复执行。
- 缺少 `tests_to_run` 时记录 P1 契约缺失，并按实际 `change_scope` 执行至少一条最小补测。补测失败记录风险，但继续 Demo 验证和后续尝试。

## 项目环境与数据隔离

- 自动环境模式只调用目标项目 scripts/demo-health.py、demo-start.py；退出码 0 为健康/成功。缺少 hook 时停止，不提供插件应用环境回退。启停和健康检查在项目根执行，hook 自行定义真实服务和依赖。
- fixture 或外部管理模式每次 runner 都保留 --no-auto-env；仍须按项目说明确认 URL、身份与服务就绪。缺失时报告受阻，不拿 smoke 代替故事验证。
- 修复前后比较真实文件变化；按项目构建/刷新规则确认运行中服务加载了新实现，必要时执行项目本地启停。不能只依赖 change_scope 或推荐角色判断刷新范围。
- 数据隔离由项目 fixture/清理入口负责，只清理本次可追踪的测试数据。批次文件间核查清理；失败时 block 保留断点，恢复先处理遗留数据。不能通过删除全库或未知服务重建隔离。
- 环境刷新不得删除 demo/test-results/runs/<run-id>/ 历史证据；每次验证使用新的 run ID。

## 日志与 Run ID

- 每次执行必须使用唯一 run ID，至少包含批次 ID、文件全路径的稳定 slug 或短哈希、轮次和用例序号。不得只使用文件 `stem`。
- runner 只可覆盖当前同名 run ID 的目录，不得清空整个 `test-results/runs/`。
- 编排层始终向诊断 agent 传入实际产生失败的 run ID，不得传入后续 `--list-tests` 的 run ID。

## 最终结果

单文件编排结果统一包含：

```text
Result: {"success":"true|false","fixed":"true|false","logs":"demo/test-results/runs/[RUN_ID]","exit_code":0,"test_file":"demo/e2e/...","run_id":"[RUN_ID]","error":""}
```

`logs` 和 `run_id` 指向最终整文件验证；未进入整文件终验时，指向最后一次失败定向验证。
