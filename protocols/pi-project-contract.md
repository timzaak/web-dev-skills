# Pi Project Contract

在设计判定 pi 交付范围、规划或恢复 pi phase、选择提交检查和发布版本文件前读取。本协议定义跨入口的项目识别与适用性；确定性识别和本地检查选择由 `${CLAUDE_PLUGIN_ROOT}/scripts/lib/pi_project.py` 实现，API 实践见 `${CLAUDE_PLUGIN_ROOT}/guides/pi/development.md`。

## 阶段适用性

- 当前设计明确交付或修改 pi extension、skill、prompt、theme 或 package 时启用 `pi`；现有资源只作为依据，不因目录存在而启用无关 feature。
- 首次交付可依据设计中已确定的包形态、资源路径和文件影响表启用，不要求先存在 `pi` 清单、`pi-package` keyword 或 `.pi/` 目录。不确定是否服务 pi 时按决策纪律确认，不补造标记。
- 项目级资源包括 `.pi/extensions/`、`.pi/skills/`、`.pi/prompts/`、`.pi/themes/`；独立包使用包根约定资源目录或 `pi` 清单中的自定义路径。项目级资源不是必须发布的 npm 包。

## 本地脚本识别

- 根 `package.json` 有对象型 `pi` 字段或 `keywords` 含 `pi-package` 时，识别为 pi 包。
- 无上述标记时，根 `package.json` 配合实际约定资源也可识别：`extensions/*.ts|js` 或 `extensions/*/index.ts|js`、`skills/**/SKILL.md`、`prompts/**/*.md`、`themes/**/*.json`。删除最后一个资源时，本次变更路径仍作为识别依据。空目录不足以识别包。
- `.pi/` 下上述项目资源的改动独立进入 pi 检查，不要求根包清单；项目资源存在时，根配置改动也进入 pi 检查。backend/frontend/demo 继续按已有区域处理；Shopify 本体保持原归属，`.pi/` 资源仍归 pi。
- 包识别仅用于选择门禁，不证明清单资源已被正确加载，也不改变 feature 范围。`pi-package` 是包目录发现标记，不是加载或阶段启用的必要条件；自定义路径包建议显式声明清单。

## 本地门禁与发布

- push 按实际变更选择门禁；代码、类型或影响代码的依赖/TS 配置变更必须类型检查。文档、skill、prompt、theme 的纯文本变更不强制 TypeScript。必要运行时与行为证据仍由 dev/accept 按 `${CLAUDE_PLUGIN_ROOT}/guides/pi/validation.md` 核对，提交检查不能替代 accept。
- 类型检查优先 pi 专项 `type-check:pi` / `typecheck:pi`，其次项目 `type-check` / `typecheck` / `check`；脚本必须覆盖实际 pi 源码。无脚本时允许已有本地 TypeScript 配合根 `tsconfig.json` 执行 `--noEmit`。缺工具或配置即失败，不联网安装编译器。项目已有 lint/build 脚本时沿用；lint 不得改写源码。
- release 只为独立包更新版本；项目级 `.pi/` 资源本身不要求根包版本。根 pi 包通过 `npm version <X.Y.Z> --no-git-tag-version --ignore-scripts --allow-same-version --workspaces=false` 同步 `package.json` 及已有 npm lock/shrinkwrap，避免依赖安装、生命周期脚本和重复 commit/tag。使用其他包管理器且有专属发布要求时沿用项目发布脚本。
- release 使用同一套本地检查选择并检查整个包；包清单和锁文件纳入版本提交。commit、`v` 前缀 tag 与 push 仍由 `${CLAUDE_PLUGIN_ROOT}/scripts/release.py` 唯一执行；不运行 `npm publish`、`pi install` 或更新用户 settings。

识别或必要命令失败时停止并报告缺口；修复输入后从原入口重试。发布失败保留实际文件差异与本地 commit/tag，由用户核对后按发布入口恢复，不静默回滚。

## 官方依据

- [Pi packages](https://pi.dev/docs/latest/packages)：约定目录、可选清单、gallery keyword 与依赖归属。
- [Extensions](https://pi.dev/docs/latest/extensions)：项目资源、加载与 `/reload`。
- [npm version](https://docs.npmjs.com/cli/v11/commands/npm-version/)：同步版本文件、关闭 Git 操作及生命周期脚本。
