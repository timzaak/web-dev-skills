# pi 初始化模板与产物

仅由 [pi 初始化流程](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/pi-init.md) 在生成与验证阶段读取。模板是最小独立 extension 包；已有工程按初始化流程增量合并，不覆盖自定义配置。

## 新包产物

| 目标文件 | 来源与处理 |
| --- | --- |
| `package.json` | [包清单模板](${CLAUDE_PLUGIN_ROOT}/skills/t-init/assets/pi/package.json)：替换 `{{PACKAGE_NAME}}`、`{{TYPESCRIPT_VERSION}}`、`{{NODE_TYPES_VERSION}}`；devDependency 为本次已核实的精确版本 |
| `tsconfig.json` | [类型检查模板](${CLAUDE_PLUGIN_ROOT}/skills/t-init/assets/pi/tsconfig.json)：检查 `extensions/`，不生成编译产物 |
| `extensions/index.ts` | [extension 入口](${CLAUDE_PLUGIN_ROOT}/skills/t-init/assets/pi/extension.ts)：有效的空工厂，等待后续设计添加能力；无后台资源和业务工具 |
| `scripts/pi-smoke.mjs` | [隔离加载脚本](${CLAUDE_PLUGIN_ROOT}/skills/t-init/assets/pi/pi-smoke.mjs)：逐字复制，不复制或 mock pi 运行时 |
| `package-lock.json` | 由真实 `npm install --ignore-scripts` 生成，不手写 |
| `AGENTS.md`、`README.md`、`.gitignore`、`scripts/index.md` | 按下文生成或增量合并 |

不预建 `.ai/` 状态、空资源目录、测试框架、build 层或独立运行时依赖。模板 Node 基线来自 pi 规范；若选定版本要求更高则相应调整 engines，并报告依据。

## 增量项目

- 独立包沿用实际 `pi` 清单或约定资源位置；没有清单时不强制加清单或 keyword，避免改变发现范围。`.pi/` 项目使用该目录作为资源根，不向根清单加 `pi` 字段。
- TS 工程已具备兼容、覆盖实际 pi 路径的检查时复用。否则从类型模板生成 `tsconfig.pi.json`，include 改为实际 pi TS 资源路径，不能继承一个排除了 `.pi/` 的原配置后假定已覆盖。根包不是 ESM 时，专项检查改用 `module: ESNext` / `moduleResolution: Bundler` 以匹配 jiti 加载，不修改宿主包的 type 或原编译策略；scripts 添加 `"type-check:pi": "tsc --noEmit --project tsconfig.pi.json"`。新增 devDependencies 仅在缺失时按兼容版本补齐。
- 只添加当前源码实际导入的 host peer；已有旧版 host 声明先按锁定版本核实，不自动升级。对纯 skill/prompt/theme 包跳过类型模板与 TS 依赖。
- 隔离脚本默认加载包根；项目级资源的脚本为 `smoke:pi: node scripts/pi-smoke.mjs .pi`。清单使用其他路径时正常从包根发现，不手工抄一份入口表绕过清单。

## 根文档与索引

- AGENTS 顶部描述真实项目形态；规范入口为 `${CLAUDE_PLUGIN_ROOT}/guides/pi/index.md`，测试前读项目 `scripts/index.md`。不要照搬全栈项目的服务、容器或业务规则。
- README 给出按实际包管理器安装、`npm run pi -- -e .`（新包临时试用，不改 settings）、索引与后续工作流；项目级资源说明正常 project trust 与 `/reload`，不指示全局信任或全局安装。
- `.gitignore` 增补 `node_modules/`、`log/` 和确有的临时产物；保留已有规则，不忽略源码、lockfile、整个 `.pi/` 或 skill 资源。
- `scripts/index.md` 集中维护实际版本、资源根与以下适用命令：安装、type-check/type-check:pi、smoke:pi、`npm run pi -- --version`、打包预览，以及后续按需新增的定向测试。没有某脚本时不列虚构入口；已有内容保留，只合并本次设施。
- 明确 `smoke:pi` 的成功仅说明真实 SDK 发现并加载本次资源，返回 `modelCalls/sessionLifecycle=not_verified`；它不要求 provider，不连接 MCP，也不验证 UI 或会话钩子。pi 运行时契约与行为证据按 pi 测试/验证指南执行。

## 加载诊断脚本边界

脚本用本地 peer 提供的真实 `DefaultResourceLoader`，内存 settings 加临时 cwd/agentDir，只加载显式传入的本地资源根；不读写日常 settings，不启动模型/session。输出为脚本本次诊断，不是跨阶段验收 envelope；门禁、证据及验收结论按共享协议消费。

参数缺失采用项目根；超过一个参数、资源根不存在、SDK 不可用、加载错误/警告或没有任何资源时退出非零。若已有项目 SDK 不支持模板使用的公开接口，依据锁定版本适配后验证，不以 fake 或移除错误检查放行。
