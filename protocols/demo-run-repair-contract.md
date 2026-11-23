# Demo Run Repair Contract

本协议是 `t-web-demo-run`、`t-web-demo-run-all`、`t-extension-demo-run`、`t-extension-demo-run-all`、`t-flutter-demo-run` 与 `t-flutter-demo-run-all` 共享的 Demo 单文件运行、诊断、修复、回归与机器可解析 Result 输出契约。批次发现、断点和汇总由批次 skill 自行编排。

## 1. 共享 Result 输出契约

Web / Extension 与 Flutter Demo runner 均以最后一行 `Result: {json}` 交付机器可解析结果。

- 必填字段：`success`, `fixed`, `logs`, `exitCode`, `testFile`, `runId`, `duration`, `error`。`success` 与 `fixed` 使用字符串 `"true" | "false"` 保持现有调用兼容。
- 编排层统一映射 `exitCode/testFile/runId` 为 `exit_code/test_file/run_id`。
- Web / Extension 可追加 `grep/mode`；runner 返回的 `logs` 相对于 `demo/`，写入 skill 结果或批次 entry 前必须规范化为仓库相对路径 `demo/<logs>`。
- Flutter 必须追加 `device/platform`；日志路径始终使用目标仓库相对路径。
- 若 runner 非零退出且没有合法 `Result` 行，视为本次 Demo 验证失败，保留退出码和输出尾部作为 `error`。

## 2. Playwright Demo（Web / Extension / Shopify）

### 单文件执行顺序

首次执行以及中断恢复时，先读目标项目 `scripts/index.md`、任务 Validation 和 fixture，确认环境模式。Shopify 使用下方 Shopify 模式；Chrome 扩展使用扩展模式；其余使用默认 Web 模式。模式、目标 URL、身份 fixture 和清理入口必须可从这些持久化输入恢复，缺失时先补齐，不能在 `continue` 或 `scan` 时默认切回全栈环境。

1. 以 `fast` 模式运行整个测试文件（`${CLAUDE_PLUGIN_ROOT}/scripts/web-demo-test-runner.py` 或项目本地同名脚本）。
2. 整文件通过时直接返回，`fixed=false`。
3. 失败时从该 run 的 `playwright-output.log` 提取失败用例标题；需要规范化完整标题时可执行 `--list-tests`。`--list-tests` 不得删除或覆盖失败 run 的日志。
4. 对失败用例串行执行诊断、修复、补测和定向 Demo 验证。
5. 定向失败全部消除后，必须再运行一次整个文件，防止修复导致其他用例回归。只有该次整文件通过才可返回 `status=passed, fixed=true`。

单文件最多进行 6 轮“诊断 -> 修复 -> 补测 -> 定向验证”。每轮只处理当前仍失败的用例，已通过用例不重复修复。整文件终验失败时，将新失败用例并入下一轮。

### 诊断、修复与补测

- Web 诊断使用 `web-demo-diagnose`；`demo/e2e/extension/` 的扩展演示使用 `extension-demo-diagnose`。输入均为 `testFile`、实际失败的 `runId` 和 `testCaseTitle`。
- 按诊断的 `recommended_agent` 选择 `web-demo-dev | extension-demo-dev | frontend-dev | extension-dev | backend-dev | miniapp-dev | flutter-dev | shopify-dev`。
- 所有 Agent 调用必须先按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 注入角色规范。
- 修复返回必须按 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md` 解析 `task_completion.change_scope` 和 `tests_to_run`。
- 补测命令必须符合 `${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md`，并按该协议规定的层顺序串行。与当前定向 Demo 验证完全相同的命令去重，不重复执行。
- 缺少 `tests_to_run` 时记录 P1 契约缺失，并按实际 `change_scope` 执行至少一条最小补测。补测失败记录风险，但继续 Demo 验证和后续尝试。
- extension/miniapp/Flutter/Shopify 补测只在目标项目实际启用对应交付端，或诊断明确归因到该交付端时执行。

### 扩展 Demo 运行模式

- 运行前从任务 Validation 和 fixture 确认环境选择。仅当 fixture 自行管理宿主站点、HTTP stub 和临时浏览器 profile 时，扩展独立测试使用 `--no-auto-env`；后续定向、整文件终验、scan 和批次恢复必须保留该参数。
- 扩展 fixture 与请求隔离规则读取 `${CLAUDE_PLUGIN_ROOT}/guides/extension/testing.md`；缺 fixture 或依赖服务时失败，不跳过用例假装通过。
- `extension-dev` 修复实际扩展代码后，必须先重新 build，再用新 persistent context 重跑；不能加载旧产物。
- 独立扩展模式的文件间隔离由 fixture 关闭 profile、重置 stub 数据实现，不运行默认 Web stop/start。真实后端依赖仍按下节重建，不能用独立模式绕过。

### Shopify Demo 运行模式

- 适用 Shopify 店面、admin 嵌入页和 customer account 页面 Demo，设计输入取 `shopify.md`；单文件、定向重测、整文件终验、批次、scan 和 continue 的所有 runner 命令均追加 `--no-auto-env`。环境启停只使用项目内 Shopify 适配版 `demo-start.py` / `demo-stop.py`（管理 `shopify app dev` 与已登记的自动化 Chrome 会话）；项目未提供时交由用户手动管理，不通过插件回退入口启动默认 Web Docker 环境。
- 真实故事运行前，按 `scripts/index.md` 核实 `shopify app dev` 已在运行、目标测试店铺/预览 URL 和该故事的身份入口（承载方式见 `${CLAUDE_PLUGIN_ROOT}/guides/shopify/development.md`）；缺身份、URL 或服务时记录环境受阻，交回编排层，不拿占位 smoke 代替。初始化静态 smoke 只验证 Playwright/日志通路，可不启动 Shopify。
- 业务数据隔离由项目 fixture/清理入口负责：为本次运行创建可追踪的独立测试数据，结束后只清理本次数据；有写操作却没有可靠的隔离/清理入口时停止。批次在文件之间核查清理成功，失败使用 `block` 保存断点；恢复时先处理上次遗留数据，再重跑未完成文件，不重建店铺或清空业务数据库。
- 修复 Shopify 业务代码后，按实际变更补跑 `${CLAUDE_PLUGIN_ROOT}/guides/shopify/quality.md` 的门禁，并确认 dev 进程已加载新应用/扩展；需要重启时用项目 Shopify 版 `demo-stop.py` / `demo-start.py`（或 `scripts/index.md` 声明的等价流程）处理，登录受阻则保留失败证据并交回编排层。每次验证使用新的 run ID，保留历史日志。

### 默认 Web 环境和数据隔离

- 每次分发修复前后必须比较实际文件变化。只要当次修复实际产生后端代码变动，就必须在当前用例的 Demo 验证前执行：

  ```bash
  uv run scripts/demo-stop.py --quiet && uv run scripts/demo-start.py
  ```

- 是否重建环境只以后端代码是否实际产生变动为准，不以 `recommended_agent`、`task_completion.change_scope` 或其他代码层的变动作为判定依据。`change_scope` 仍用于选择补测范围，不能替代文件变化事实。
- 使用默认 Web 环境的批次运行时，Demo 用例产生的业务数据可能影响后续文件。每个文件完成后，若还有下一个文件，必须通过上述 stop/start 重建 Demo 环境和数据容器。
- 环境重建不得删除 `demo/test-results/runs/<run-id>/` 历史证据。

### 日志、Run ID 与编排结果

- 每次执行必须使用唯一 run ID，至少包含批次 ID、文件全路径的稳定 slug 或短哈希、轮次和用例序号，不得只使用文件 `stem`；runner 只可覆盖当前同名 run ID 目录，不得清空整个 `test-results/runs/`；向诊断 agent 传入实际失败的 run ID，不得传入后续 `--list-tests` 的 run ID。
- 单文件编排最终结果：

```text
Result: {"success":"true|false","fixed":"true|false","logs":"demo/test-results/runs/[RUN_ID]","exit_code":0,"test_file":"demo/e2e/...","run_id":"[RUN_ID]","error":""}
```

`logs` 和 `run_id` 指向最终整文件验证；未进入整文件终验时，指向最后一次失败定向验证。

## 3. Android Patrol Demo（Flutter）

### 测试形态与前置条件

- 测试文件位于 `patrol_test/<domain>/<story>_test.dart`，文件顶部引用 `docs/user-stories/...` 及稳定 US ID（交付测试文件不得引用 `.ai/user-stories/...`，见 `${CLAUDE_PLUGIN_ROOT}/protocols/code-comment-contract.md`）。一个文件覆盖一个用户故事或单一强耦合状态流；使用生产 composition root 或只改环境配置的 Demo entrypoint，禁止 Provider fake、mock repository 或直接构造单页。
- 日志写入 `patrol_test/test-results/runs/<run-id>/patrol-output.log`，测试资产 authoring 时确保 `patrol_test/test-results/` 被忽略。
- Runner 末行格式：

```text
Result: {"success":"true|false","fixed":"true|false","logs":"patrol_test/test-results/runs/...","exitCode":0,"testFile":"patrol_test/...","runId":"...","duration":1.2,"device":"...","platform":"android","error":""}
```

- 前置检查：读取 `pubspec.yaml`、`pubspec.lock` 和 `patrol.test_directory`（默认 `patrol_test/`）；执行 `patrol doctor`，CLI 须与项目锁定的 Patrol 4.x 兼容，不自动升级；`--device` 必须是受支持的 Android 设备，未传时仅可自动选择唯一 Android 设备，零个或多个候选均停止；`scripts/flutter-demo-start.py` 与 `scripts/flutter-demo-stop.py` 可选但须成对存在，不存在表示 App 无需外部环境。

### 单文件循环与批量

1. 执行整个 Patrol 文件：`flutter-demo-test-runner.py <file> --device <id>`。
2. 通过则返回 `fixed=false`。
3. 失败则调用 `flutter-demo-diagnose`，以 Patrol 输出、Flutter 日志、测试代码和相关用户故事为证据。
4. 按诊断分发到 `flutter-demo-dev | flutter-dev | backend-dev | manual`，执行符合 `tests-to-run-contract.md` 的最小补测后重跑整文件。
5. 最多 6 轮。Patrol 首版无稳定标题过滤契约，不伪造逐用例 grep，修复闭环以文件为单位。环境或设备前置失败时不得修改业务代码；停止脚本失败须写入结果，不得静默忽略。
6. 批量发现 `patrol_test/**/*_test.dart`（排除 `test-results/`），逐文件串行运行并持久化 checkpoint，支持 fresh 和 `continue`；首版不提供 Playwright scan/cluster。
