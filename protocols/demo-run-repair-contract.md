# Demo Run Repair Contract

本协议是 `t-demo-run` 与 `t-demo-run-all` 共享的单文件 Demo E2E 运行、诊断、修复和回归契约。批次发现、断点和汇总由 `t-demo-run-all` 自行编排。

## Runner 输出适配

`${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py` 最后一行输出：

```text
Result: {"success":"true|false","logs":"...","exitCode":0,"testFile":"...","runId":"...","duration":1.2,"error":""}
```

编排层解析后统一映射为：

- `exitCode` -> `exit_code`
- `testFile` -> `test_file`
- `runId` -> `run_id`
- runner 返回的 `logs` 相对于 `demo/`；写入 skill 结果或批次 entry 前必须规范化为仓库相对路径 `demo/<logs>`
- `success` 仍按字符串 `"true" | "false"` 解析

若 runner 非零退出且没有合法的 `Result` 行，视为本次 Demo 验证失败，保留退出码和输出尾部作为 `error`。

## 单文件执行顺序

1. 以 `fast` 模式运行整个测试文件。
2. 整文件通过时直接返回，`fixed=false`。
3. 失败时从该 run 的 `playwright-output.log` 提取失败用例标题；需要规范化完整标题时可执行 `--list-tests`。`--list-tests` 不得删除或覆盖失败 run 的日志。
4. 对失败用例串行执行诊断、修复、补测和定向 Demo 验证。
5. 定向失败全部消除后，必须再运行一次整个文件，防止修复导致其他用例回归。只有该次整文件通过才可返回 `status=passed, fixed=true`。

单文件最多进行 6 轮“诊断 -> 修复 -> 补测 -> 定向验证”。每轮只处理当前仍失败的用例，已通过用例不重复修复。整文件终验失败时，将新失败用例并入下一轮。

## 诊断、修复与补测

- 诊断使用 `demo-diagnose`，输入 `testFile`、实际失败的 `runId` 和 `testCaseTitle`。
- 按诊断的 `recommended_agent` 选择 `demo-dev | frontend-dev | backend-dev | miniapp-dev | flutter-dev`。
- 所有 Agent 调用必须先按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 注入角色规范。
- 修复返回必须按 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md` 解析 `task_completion.change_scope` 和 `tests_to_run`。
- 补测命令必须符合 `${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md`，并按 `backend -> frontend -> miniapp -> flutter -> demo` 串行。与当前定向 Demo 验证完全相同的 `demo` 命令去重，不重复执行。
- 缺少 `tests_to_run` 时记录 P1 契约缺失，并按实际 `change_scope` 执行至少一条最小补测。补测失败记录风险，但继续 Demo 验证和后续尝试。
- miniapp/Flutter 补测只在目标项目实际启用对应交付端，或诊断明确归因到该交付端时执行。

## 环境和数据隔离

- 每次分发修复前后必须比较实际文件变化。只要当次修复实际产生后端代码变动，就必须在当前用例的 Demo 验证前执行：

  ```bash
  uv run scripts/demo-stop.py --quiet && uv run scripts/demo-start.py
  ```

- 是否重建环境只以后端代码是否实际产生变动为准，不以 `recommended_agent`、`task_completion.change_scope` 或其他代码层的变动作为判定依据。`change_scope` 仍用于选择补测范围，不能替代文件变化事实。
- 批次运行时，Demo 用例产生的业务数据可能影响后续文件。每个文件完成后，若还有下一个文件，必须通过上述 stop/start 重建 Demo 环境和数据容器。
- 环境重建不得删除 `demo/test-results/runs/<run-id>/` 历史证据。

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
