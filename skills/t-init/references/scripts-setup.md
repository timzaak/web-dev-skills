# 脚本适配与 `scripts/index.md` 生成规范

`t-init` 三个场景（全栈、Shopify、extension-demo）把插件脚本复制进目标项目、完成适配并生成 `scripts/index.md` 时，本文件是唯一规范。测试说明只维护在目标项目 `scripts/index.md`，`AGENTS.md` 只提供读取入口。

## 1. 脚本复制与适配规则

插件 `${CLAUDE_PLUGIN_ROOT}/scripts/` 提取自源全栈工程，内置了源工程事实（后端二进制名、配置环境变量、容器名、端口、健康端点）。直接原样复制的脚本在目标项目中不可运行或行为错误；交付前必须按目标工程实际产物完成改写清单和交付验证。

### 适配输入

- **全栈场景**：生成的 `backend/`、`frontend/`、`demo/` 产物 — workspace 成员与二进制名、启动命令、配置文件与注入方式（`--config` 或环境变量）、端口、健康端点、前端 dev 命令。
- **Shopify 场景**：CLI 工程事实（npm scripts、`shopify.app.toml`）与 [Shopify 开发规范](${CLAUDE_PLUGIN_ROOT}/guides/shopify/development.md)。
- **extension-demo 场景**：现有工程的构建入口与环境配置。

### 改写清单

左侧事实必须能在目标工程产物中找到出处，找不到出处的源项目残留一律删除，不照抄：

| 脚本族 | 必须改写项 |
| --- | --- |
| `demo-start.py`、`demo-stop.py`、`lib/demo_env.py`（全栈） | 后端启动命令与工作目录（以生成的 workspace 成员为准，不用源项目二进制名）；配置注入方式与生成的入口一致，删除与目标工程无关的源项目环境变量和密钥；后端/前端端口、容器名、镜像、数据库名使用项目语义，避免与其他初始化项目冲突；健康端点与生成路由一致；`demo-stop.py` 的停止识别（端口、进程路径）与实际启动方式一致；日志文件名与实际写入路径一致；help 文案中的项目名 |
| `demo-start.py`、`demo-stop.py`（Shopify 版） | 生成全新实现，不复制默认 Web 逻辑：不引入 Docker 数据库/Redis，不启动任何后端进程。`demo-start.py` 启动项目 `shopify app dev`（复用工程 npm script），等待输出就绪并把预览 URL 写入日志与 `log/`（隧道域名按域名特征识别，不硬编码）；`scripts/index.md` 登记了自动化 Chrome 附加会话时，按开发规范一并启动专用实例。`demo-stop.py` 结束 dev 进程树和本脚本启动的 Chrome；残留 node 进程按开发规范的模块匹配方式定位，不盲目结束全部 node 进程 |
| `test-start.py`、`test-stop.py`（全栈） | 测试容器名、端口映射、数据库名使用项目语义 |
| runner 族：`web-demo-test-runner.py`、`web-demo-run-all.py`、`web-demo-failure-summary.py`、`cleanup-demo.py`、`cleanup-test-logs.py` | 默认无需改写。项目不保留默认 Web 环境时（Shopify、独立扩展），把 `lib/demo_env.py` 的自动环境路径改写为显式不适用（提示使用 `--no-auto-env`），删除指向不存在服务的启动逻辑 |

不可变契约以 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md` 的 Script Entry Rules 为准：脚本文件名、主要 CLI 参数、输出 JSON 和日志契约保持稳定；运行入口为 `uv run scripts/<name>.py`。

### 交付验证与增量场景

1. **静态核对**：逐项确认改写清单中的每个事实与目标工程产物一致（启动命令、端口、容器名、配置注入、健康端点在生成的代码或配置中真实存在），脚本内无源项目残留。
2. **执行验证**：环境允许时运行一次真实循环 — 全栈为 `demo-start.py` 启动健康后 `demo-stop.py` 停止；Shopify 为 CLI 登录可用时 `demo-start.py`（记录预览 URL）后 `demo-stop.py`，登录或网络受阻时至少空跑一次 `demo-stop.py`。环境不可执行时在收尾输出明确标为未验证，不以「文件已复制」当作已适配。
3. **增量场景**：已存在同名脚本先按各场景规则比较；内容仍是插件原样拷贝（未适配）时补做适配并报告改写项；已有自定义实现保留，只在接口不兼容时报告差异。

## 2. 生成目标项目 `scripts/index.md`

生成时读取 [测试命令契约](${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md) 和 [Demo 执行契约](${CLAUDE_PLUGIN_ROOT}/protocols/demo-run-repair-contract.md)；包含后端测试时再读 [后端执行契约](${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md)。核对项目实际脚本、package.json 和测试配置，只列已启用的测试层并用真实路径替换示例参数；未配置的测试标明缺口，不虚构命令。

### 如何运行

默认从项目根目录执行，优先运行与改动相关的最小可靠范围；仅在范围无法收敛或门禁要求时运行全量，并记录原因。

| 用途 | 命令 |
| --- | --- |
| 后端定向测试 | `uv run scripts/backend-test.py -- <test_name>` |
| 后端按 crate / 场景筛选 | `uv run scripts/backend-test.py -- -E 'package(<crate>) and test(<pattern>)'` |
| 前端定向测试（已配置 test:run 时） | `cd frontend && npm run test:run -- <文件或匹配模式>` |
| Demo 整文件测试 | `uv run scripts/web-demo-test-runner.py "demo/e2e/<file>.e2e.ts" --mode fast --run-id <唯一ID>` |
| Demo 详细日志调试 | `uv run scripts/web-demo-test-runner.py "demo/e2e/<file>.e2e.ts" --log-level verbose` |
| Demo 失败用例重测 | 上述命令追加 `--grep "<完整测试标题>"`，使用新的 run ID；通过后重跑整文件 |
| 扩展 Demo 构建 | 项目实际构建命令与工作目录；必须先成功构建，再运行下列测试 |
| 扩展 Demo 整文件测试 | `uv run scripts/web-demo-test-runner.py demo/e2e/extension/<file>.e2e.ts --run-id <唯一ID>`；fixture 独立管理环境时追加 `--no-auto-env` |

后端执行前用 `cargo nextest list` 的对应筛选参数确认选中预期测试；漏选或零用例不算覆盖通过。`cargo check --tests`、前端 type-check / build 仅是编译或静态检查，不替代测试。

### 环境与结果

- 按实际入口补充必要工具、安装命令和配置：后端 uv / Rust / cargo-nextest / Docker；前端 Node / npm；Demo 另需 Playwright 浏览器。Vitest 使用 MSW 隔离 API 时无需真实后端。
- 后端 runner 自行准备依赖，无需先执行 `test-start.py`；Demo runner 自检并按需启动环境。Shopify 的外部环境及独立扩展 fixture 使用 `--no-auto-env`，具体条件按 Demo 执行契约对应模式。
- 按实际脚本写明日志位置和停止/清理命令及其影响范围。后端查看 runner 输出的日志路径；前端查看终端或已配置报告；Demo 查看末行 `Result`，其中 `logs` 相对 `demo/`，常见位置为 `demo/test-results/runs/<run-id>/`。
- 失败时保留命令、失败用例和日志，修复后定向重跑；本地脚本失败不得换插件脚本绕过。未执行或受阻的测试明确记录原因。

Demo 日志由 `playwright-unified-logger` 产生，索引中写明可用的日志环境变量：

| 变量 | 值 | 默认 |
| --- | --- | --- |
| `UNIFIED_LOG_LEVEL` | mini / normal / verbose / silent | mini |
| `UNIFIED_LOG_DEDUP` | true / false | true |
| `UNIFIED_LOG_AGGREGATE` | true / false | true |
| `UNIFIED_LOG_COMPACT` | true / false | false |
| `UNIFIED_LOG_OUTPUT_DIR` | 目录路径 | test-results/unified-logs |

### 批量 Demo 与维护

- 批量执行与修复使用 `/t-tools:t-web-demo-run-all`，中断后用 `/t-tools:t-web-demo-run-all continue`；`web-demo-run-all.py discover` 只发现用例，不执行测试。批次编排由 skill 负责，不在此复制调度流程。
- 扩展目录使用 `/t-tools:t-extension-demo-run-all` 及其 `continue`，单文件用 `/t-tools:t-extension-demo-run`，故事验收用 `/t-tools:t-extension-demo-accept`。独立扩展只列扩展入口，不指向默认 Web 启停脚本。记录扩展源码/产物路径、ID 来源（需要时）、宿主/stub 与真实服务依赖，重跑沿用环境模式；初始化 smoke 通过不代表故事已验收。
- Shopify 项目另列实际类型检查、应用构建、扩展构建入口，以及测试店铺 URL 配置、身份 fixture、启动与清理步骤；启停入口列项目实际生成的 Shopify 版 `demo-start.py` / `demo-stop.py`（`shopify app dev` 与自动化 Chrome 附加会话），不列默认 Web Docker 启停命令；所有 Demo 测试命令保留 `--no-auto-env`，批次和恢复遵循共享修复协议的 Shopify Demo 运行模式。
- 新增或修改测试入口时同步更新本索引。
