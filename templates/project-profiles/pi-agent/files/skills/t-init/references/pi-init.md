# pi 初始化流程

仅在 `t-init --pi <project-name|.>` 时读取并执行。输出为 pi extension/package 或项目级 `.pi/` 资源的开发基础设施；后续功能走设计和 `pi` phase，本流程不实现产品功能、不创建阶段状态，也不产出功能验收结论。

执行前读 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`、`${CLAUDE_PLUGIN_ROOT}/protocols/pi-project-contract.md` 和 `${CLAUDE_PLUGIN_ROOT}/guides/pi/development.md`。生成文件时再读 [pi 模板与产物规则](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/pi-template.md)；不读取全栈、Shopify 或 Web Demo 模板。

## 1. 定位目标与恢复范围

- 目标是 `.` 时使用当前目标项目根目录；否则仅允许长度 1–50 的英文、数字、连字符、下划线名称，拒绝 `..`、路径分隔符、绝对路径和额外参数。新 npm 包名转为小写 kebab-case，但目录沿用输入；规范化后仍无有效 npm 包名时在创建目录前停止。先报告实际绝对路径，已有包名不重命名。
- 不存在或空目录：新建独立 TypeScript extension 包。
- 已有 pi 包或项目级 `.pi/` 资源：增量补齐，沿用实际资源、包管理器、版本、清单与 scripts。纯 skill/prompt/theme 项目不新增 extension、TS 工程或占位测试。
- 只有部分初始化产物时，逐文件核对模板和项目事实，复用已完成部分，仅补缺失项。非空目录无法确定为 pi 项目，或现有配置与必要门禁冲突时，先报告具体冲突并按决策纪律确认目标；不清空目录或覆盖已有文件。
- 重跑始终以磁盘文件为恢复点，不新增初始化状态文件，不依赖会话记忆。相同内容跳过；JSON 只合并缺失且不冲突的字段，数组去重，现有自定义内容保留；同名脚本不同实现时核对接口，不能静默替换。

## 2. 核对运行环境与版本

通过 Context7 查询 pi 官方 packages/extensions/SDK 文档；失败时回退官方站点或官方仓库。按目标已锁定版本核对 API 与 Node 要求，不根据旧知识猜版本。新建项目可查 `npm view @earendil-works/pi-coding-agent version engines --json`、TypeScript 和当前 Node 主版本的 `@types/node` 元数据，选择兼容的精确 devDependency 版本并替换模板变量；锁文件记录实际 host peer 版本。

- Node/npm 缺失或 Node 不满足已选 pi 版本时，记录前置受阻；不切换用户全局 Node、安装全局 pi 或改写全局配置。仍可生成已确认的文件，但未完成依赖安装与验证就不能报告初始化完成。
- 独立包的 host 依赖遵循 pi 开发规范的 peerDependencies 归属；npm 作者侧安装会为本地开发提供 host peer，不为锁版本把它移入 dependencies 或重复声明到 devDependencies。
- 已有项目不默认升级依赖、迁移旧 host 命名空间或转换锁文件。必要版本/API 依据无法取得且项目也无可用锁定依据时停止该部分生成并暴露缺口。

## 3. 生成或合并开发设施

主会话按 pi 模板与产物规则直接生成，不需为静态骨架派发实现角色或套用功能 Design-First。只补初始化设施；若用户同时要求功能，先完成初始化并交回功能主链。

- 新包：最小清单、extension 入口、类型检查、隔离加载诊断脚本与根文档。仅创建实际使用的资源目录，不写空 skill/prompt/theme 或假业务工具。
- 已有项目：保留资源与清单，不把 `.pi/` 转成根发布包。TS 源码已有时核对类型检查是否覆盖它；现有检查不覆盖 pi 目录时新增独立 `tsconfig.pi.json` 与 `type-check:pi`，不覆盖原脚本或扩大原 tsconfig 的编译范围。无根 npm 工程而需要 TS 开发设施时，先确认放置位置和包管理方式；不能为纯文本资源强建 Node 工程。
- 根据已安装的 SDK 版本核对隔离加载脚本兼容性，只在本地 host 可用时补齐。纯资源项目无本地 host 时保留其形态，用既有 pi CLI 在隔离环境验证，无法执行则记录未验证，不安装一套无关开发依赖。
- scripts 说明只在项目 `scripts/index.md` 维护；AGENTS/README 只保留规范与索引入口。保留 `${CLAUDE_PLUGIN_ROOT}` 字面引用，不写本机插件路径。
- 不复制 backend/Web Demo/Shopify 环境脚本，不生成 Playwright 或 Vitest 占位用例，不修改用户 `settings.json`、鉴权、project trust 或 git remote，不执行 `pi install` / `npm publish`。

## 4. 安装与验证

新包在包根执行 `npm install --ignore-scripts`，保留生成的 lockfile；已有项目用既定包管理器，只在依赖有增量时安装，不为重跑重复添加依赖。安装失败保留产物，修复原因后从本步骤恢复。

按实际脚本验证：

1. 确认清单路径真实存在、host 依赖归属正确，TypeScript 开发项目的检查覆盖实际 extension 路径；有 TS 时运行 `npm run type-check` 或新增的 `npm run type-check:pi`。
2. 有隔离加载脚本时运行 `npm run smoke:pi`，核对返回的资源列表、诊断和非零资源数；新包必须包含刚创建的 extension。该检查不调用模型或启动 session，不证明会话生命周期、UI、工具执行或 provider 鉴权。
3. 若用户要求模型或 UI 冒烟，再按 `${CLAUDE_PLUGIN_ROOT}/guides/pi/testing.md` 执行并单列证据。缺 provider 不阻断无需 provider 的骨架验证，但必须明确模型调用未验证；不能用假结果或注册 fake 补足。
4. 核对 AGENTS/README 指向真实 `scripts/index.md`，索引中的命令、资源根、版本和结果边界准确。新包用 `npm pack --dry-run --ignore-scripts --json` 核对发布清单包含实际资源且不含 node_modules/日志/密钥；不运行 publish。

必要检查失败或缺工具时仅报告已生成及未完成项，不能报告初始化完成；修复后重新运行本步骤。新包的静态与加载检查通过后才可作为下游设计/执行基础，真实行为证据仍由后续 dev/accept 收口。纯资源项目以适用的资源加载和索引检查为初始化门禁，不要求 TS。

## 收尾

报告目标绝对路径、包/项目级资源形态、新建/增量/恢复模式、新增/合并/保留项、实际 Node/pi 版本、安装/类型/加载/打包检查结果及未验证边界。失败给出同一命令的恢复入口；成功后建议 `t-decision` 或已有 feature 的 `t-design`，再 `t-super-run --phase pi`。不自动执行下游 skill，不宣称功能验收通过。
