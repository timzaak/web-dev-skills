# 脚本复制与适配规则

t-init 三个模式（全栈、Shopify、extension-demo）把插件脚本复制进目标项目时，本文件是唯一适配规则。插件 `${CLAUDE_PLUGIN_ROOT}/scripts/` 提取自源全栈工程，内置了该工程的事实（后端二进制名、配置环境变量、容器名、端口、健康端点）。直接原样复制的脚本在目标项目中不可运行或行为错误；复制只是起点，交付前必须完成本文件的改写清单和交付验证。

## 适配输入

适配依据是目标工程的实际事实，不假设插件脚本中的默认值已经正确：

- 全栈模式：Step 3 ~ 5 生成的 `backend/`、`frontend/`、`demo/` 产物 — workspace 成员与二进制名、启动命令、配置文件与注入方式（`--config` 参数或环境变量）、端口、健康端点、前端 dev 命令。
- Shopify 模式：CLI 工程事实（npm scripts、`shopify.app.toml`）与 [Shopify 本地环境与商家会话](${CLAUDE_PLUGIN_ROOT}/guides/shopify/environment.md)。
- extension-demo 模式：现有工程的构建入口与环境配置。

## 改写清单

按脚本族逐项核对；左侧事实必须能在目标工程产物中找到出处，找不到出处的源项目残留一律删除，不照抄。

| 脚本族 | 必须改写项 |
| --- | --- |
| `demo-start.py`、`demo-stop.py`、`lib/demo_env.py`（全栈） | 后端启动命令与工作目录（以生成的 workspace 成员为准，不用源项目二进制名）；配置注入方式与生成的入口一致，删除与目标工程无关的源项目环境变量和密钥；后端/前端端口、容器名、镜像、数据库名使用项目语义，避免与其他初始化项目冲突；健康端点与生成路由一致；`demo-stop.py` 的停止识别（端口、进程路径）与实际启动方式一致；日志文件名与实际写入路径一致；help 文案中的项目名 |
| `demo-start.py`、`demo-stop.py`（Shopify 版） | 生成全新实现，不复制默认 Web 逻辑：不引入 Docker 数据库/Redis，不启动任何后端进程。`demo-start.py` 启动项目 `shopify app dev`（复用工程 npm script），等待输出就绪并把预览 URL 写入日志与 `log/`（隧道域名按域名特征识别，不硬编码）；`scripts/index.md` 登记了自动化 Chrome 附加会话时，按环境指南一并启动专用实例。`demo-stop.py` 结束 dev 进程树和本脚本启动的 Chrome；残留 node 进程按环境指南的模块匹配方式定位，不盲目结束全部 node 进程 |
| `test-start.py`、`test-stop.py`（全栈） | 测试容器名、端口映射、数据库名使用项目语义 |
| runner 族：`web-demo-test-runner.py`、`web-demo-run-all.py`、`web-demo-failure-summary.py`、`cleanup-demo.py`、`cleanup-test-logs.py`、`debug-test.py` | 默认无需改写。项目不保留默认 Web 环境时（Shopify、独立扩展），把 `lib/demo_env.py` 的自动环境路径改写为显式不适用（提示使用 `--no-auto-env`），删除指向不存在服务的启动逻辑 |

不可变契约以 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md` 的 Script Entry Rules 为准：脚本文件名、主要 CLI 参数、输出 JSON 和日志契约保持稳定；运行入口为 `uv run scripts/<name>.py`。

## 交付验证

1. 静态核对：逐项确认改写清单中的每个事实与目标工程产物一致（启动命令、端口、容器名、配置注入、健康端点在生成的代码或配置中真实存在）。
2. 执行验证：环境允许时运行一次真实循环 — 全栈为 `demo-start.py` 启动健康后 `demo-stop.py` 停止；Shopify 为 CLI 登录可用时 `demo-start.py`（记录预览 URL）后 `demo-stop.py`，登录或网络受阻时至少空跑一次 `demo-stop.py`。
3. 环境不可执行时，在收尾输出把该项明确标为未验证；不以「文件已复制」当作已适配。

## 增量场景

已存在同名脚本先按各模式的增量规则比较。内容仍是插件原样拷贝（未适配）时，按本文件补做适配并报告改写项；已有自定义实现保留，只在接口不兼容时报告差异。
