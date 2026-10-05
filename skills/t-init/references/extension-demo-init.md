# extension-demo 初始化流程

仅在 `t-init --extension-demo [--extension-dir <path>]` 时读取。输入为已有 WXT 工程、实际构建入口、可观察的现有扩展行为及当前 Demo 配置；输出为项目 `demo/` 内的扩展测试基础设施和 `scripts/index.md`。不要求先生成 PRD，也不创建功能阶段状态或用户故事验收结论。

## 1. 确认项目事实

- 当前目录必须是目标项目根目录。先读项目 `AGENTS.md`、`scripts/index.md`、package.json、锁文件、WXT 配置与现有 Demo 配置。
- 指定 `--extension-dir` 时将路径相对项目根目录解析，必须存在且位于目标项目内；允许 `.`。未指定时检查根目录与 `extension/` 的 WXT 工程标记（package.json 的 WXT 依赖/脚本及实际入口）；只有一个候选时采用，多个候选让用户选择，不按目录名猜测。
- 没有 WXT 工程时停止，指向 [扩展初始化指南](${CLAUDE_PLUGIN_ROOT}/guides/extension/initialization.md)，不要生成空 Demo 假装成功。
- 从 scripts 与配置取得构建命令、工作目录、Chrome MV3 产物目录、已有 popup/options/content script/background 入口，以及最小可观察加载结果。默认产物目录只能作为候选；不要把 `.output/chrome-mv3-dev` 热更新产物作为正式验证输入。
- 按 [扩展演示指南](${CLAUDE_PLUGIN_ROOT}/guides/extension/demo-testing.md) 确认宿主/stub 或真实后端依赖；无法从现有代码和配置确定的测试账号、宿主站点或环境选择由用户裁决。信息未确认前不写入假设配置。
- 增量合并 `demo/`、scripts 和文档，保留现有测试、锁文件、用户说明和脚本适配。文件名冲突先检查能否复用；只在无法兼容合并时暴露冲突，不整目录覆盖。

## 2. 查询与生成

使用 Context7 核对目标锁定版本的 Playwright 扩展 fixture API；WXT 构建方式不确定时同时查询 WXT。查询失败回退到 [Playwright 官方文档](https://playwright.dev/docs/chrome-extensions) 和 [WXT E2E 文档](https://wxt.dev/guide/essentials/e2e-testing.html)。均不可用时可准备文件，但明确记录 API 未核实，必须以实际执行结果判断是否完成。

按 [subagent 调度协议](${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md)，用 [subagent prompt 模板](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/subagent-prompts.md) 的 `extension-demo-dev` 部分传入上述事实；该角色按 [extension-demo 模板](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/extension-demo-template.md) 增量生成配置、fixture 和最小加载测试。业务逻辑不在初始化范围，发现生产缺陷时返回证据。

主 Agent 从 `${CLAUDE_PLUGIN_ROOT}/scripts/` 复制缺失的 `web-demo-test-runner.py`、`web-demo-run-all.py`、`web-demo-failure-summary.py`、`lib/*.py` 到目标项目。已存在脚本先检查 CLI/结果兼容性，不直接覆盖；独立模式不复制或启动默认 Web 环境。需要真实后端时复用并核实项目现有环境脚本，缺失配置先补齐或报告阻塞，不能套用默认 Docker 容器。

按 [scripts 模板](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/scripts-template.md) 仅生成或更新 extension-demo 相关说明。记录扩展目录、构建命令和产物、环境模式、依赖安装、定向 runner 命令、日志位置与失败恢复。根目录 AGENTS.md 缺失时按 [AGENTS 模板](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/agents-template.md) 创建，已存在时仅补充 `scripts/index.md` 读取入口；README 只链接该索引，避免重复维护命令。

## 3. 验证与交接

在目标项目用既有包管理器安装新增依赖及 Playwright Chromium，确认本地 runner 所需的 uv、Node 与 npx 可用。先按 [验证证据协议](${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md) 复用 subagent 本轮仍有效的构建、类型检查和发现结果，输入变化或证据不足时补跑；最后必须通过本地 runner 验证完整入口：

1. 实际扩展构建命令，确认本次 MV3 manifest 与 fixture 路径一致；记录命令、产物和结果。
2. Demo TypeScript 检查和扩展用例发现，确认用例选入 `demo-fast`，未重复选入其他 browser project。先确认现有 Web 用例发现范围不变；共享配置发生变化时补跑一个受影响的现有 Web smoke。
3. 从项目根目录执行 `uv run scripts/web-demo-test-runner.py demo/e2e/extension/verification/smoke.e2e.ts --run-id <唯一ID>`，环境参数遵循 [Demo 执行契约](${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md)。独立 fixture 模式追加 `--no-auto-env`。测试必须加载本次构建并断言实际入口的可观察行为，不能仅检测浏览器能启动。
4. 检查 runner 的 Result、浏览器日志与统一日志，确认 context、宿主/stub 已清理；按下方清单核对产物。

成功必须同时满足构建、类型检查、实际浏览器测试通过，以及本地入口和文档一致。浏览器、依赖或必要环境不可用时报告“已生成，初始化未完成”，不以 skip 或零用例作为通过。

收尾列出修改文件、项目/扩展路径、真实命令和结果、run ID 与日志位置、环境选择、未完成项。初始化测试只证明基础设施和选定入口加载；不代表用户故事验收，不替代 `extension-demo-accept`。设计声明扩展 Demo 后再进入 `t-super-run --phase extension-demo`；没有故事时不自动启用该 phase。

## 输出清单

- `demo/package.json` 与实际包管理器锁文件：Playwright、TypeScript、Node 类型和 `playwright-unified-logger` 依赖，以及真实可用的类型检查入口。
- `demo/tsconfig.json`、`demo/playwright.config.ts`、`demo/.gitignore`：按模板合并，不要求生成普通 Web Demo 的 auth/page object。
- `demo/e2e/extension/extension-target.ts`：本次工程的构建产物定位。
- `demo/e2e/extension/fixtures.ts`：扩展加载、隔离与清理；所需宿主/stub helper 按实际入口创建。
- `demo/e2e/extension/verification/smoke.e2e.ts`：至少一个真实加载结果断言；有可测交互时覆盖其稳定结果。基础设施测试与故事验收的边界按 [扩展 Demo 验收契约](${CLAUDE_PLUGIN_ROOT}/protocols/extension-demo-acceptance-contract.md)，不放入故事批次。
- 上述项目本地脚本及 `scripts/index.md`、根目录 `AGENTS.md` / `README.md` 的读取链接。

## 失败与重入

- 参数、工程识别或环境信息缺失：主 Agent 报告缺口；用户补齐后从事实检查恢复。
- 生成或测试失败：保留已生成文件和失败日志，主 Agent 继续协调 `extension-demo-dev` 修复基础设施；生产缺陷交回 extension 阶段，不为了跑通而增添生产权限、后台入口或测试专用业务分支。
- 重复调用：先复用已有 fixture、依赖和 smoke，只补缺失项；配置或扩展有变化时重新构建和定向验证，不重建工程、不清空历史 run，不重复插入索引或 AGENTS 说明。
