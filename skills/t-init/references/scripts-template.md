# Scripts 模板

Step 6 适配本地脚本后，按下述结构生成目标项目 `scripts/index.md`；测试说明只在该文件维护，AGENTS.md 只提供读取入口。

生成时读取 [测试命令契约](${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md)、[后端执行契约](${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md) 和 [Demo 执行契约](${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md)，再核对项目实际脚本、package.json 和测试配置。只列已启用的测试层，用真实路径替换示例参数；未配置的测试标明缺口，不虚构命令。

## scripts/index.md 内容

### 如何运行

默认从项目根目录执行，优先运行与改动相关的最小可靠范围；仅在范围无法收敛或门禁要求时运行全量，并记录原因。

| 用途 | 命令 |
| --- | --- |
| 后端定向测试 | `uv run scripts/backend-test.py -- <test_name>` |
| 后端按 crate / 场景筛选 | `uv run scripts/backend-test.py -- -E 'package(<crate>) and test(<pattern>)'` |
| 前端定向测试（已配置 test:run 时） | `cd frontend && npm run test:run -- <文件或匹配模式>` |
| Demo 整文件测试 | `uv run scripts/web-demo-test-runner.py "demo/e2e/<file>.e2e.ts" --mode fast --run-id <唯一ID>` |
| Demo 失败用例重测 | 上述命令追加 `--grep "<完整测试标题>"`，使用新的 run ID；通过后重跑整文件 |

后端执行前用 `cargo nextest list` 的对应筛选参数确认选中预期测试；漏选或零用例不算覆盖通过。`cargo check --tests`、前端 type-check / build 仅是编译或静态检查，不替代测试。

### 环境与结果

- 按实际入口补充必要工具、安装命令和配置：后端 uv / Rust / cargo-nextest / Docker；前端 Node / npm；Demo 另需 Playwright 浏览器。Vitest 使用 MSW 隔离 API 时无需真实后端。
- 后端 runner 自行准备依赖，无需先执行 `test-start.py`；Demo runner 自检并按需启动环境。仅 fixture 和配置确认可独立运行时使用 `--no-auto-env`。
- 按实际脚本写明日志位置和停止/清理命令及其影响范围。后端查看 runner 输出的日志路径；前端查看终端或已配置报告；Demo 查看末行 `Result`，其中 `logs` 相对 `demo/`，常见位置为 `demo/test-results/runs/<run-id>/`。
- 失败时保留命令、失败用例和日志，修复后定向重跑；本地脚本失败不得换插件脚本绕过。未执行或受阻的测试明确记录原因。

### 批量 Demo 与维护

批量执行与修复使用 `/t-tools:t-web-demo-run-all`，中断后用 `/t-tools:t-web-demo-run-all continue`；`web-demo-run-all.py discover` 只发现用例，不执行测试。批次编排由 skill 负责，不在此复制调度流程。

新增或修改测试入口时同步更新本索引。
