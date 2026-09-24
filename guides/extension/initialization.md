# Chrome 扩展工程初始化

从零搭建 WXT 工程时使用；`t-init` 尚无扩展模板。已有工程跳过初始化，后续按需求来源进入设计与任务阶段。

## 1. 创建工程

```bash
npx wxt@latest init <目录名> -t react --pm <npm|pnpm|yarn|bun>
```

- 全栈仓库默认放在 `extension/`，独立扩展以生成目录为仓库根目录；进入该目录，用选定的包管理器安装依赖。下文命令以 npm 为例。
- 技术基线按 [development.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/development.md)；初始化保留 React + TypeScript 模板，功能依赖与权限增量待设计明确后引入。

## 2. 确认开发循环

写业务代码前用 AskUserQuestion 确认开发循环模式，按选择写入 `wxt.config.ts`；未确认前不替用户默认：

| 模式 | 配置 | 说明 |
|---|---|---|
| 独立 dev 浏览器 | 无需额外配置 | WXT 自动拉起装好扩展的浏览器，保存后自动重载；一次性 profile，登录态不跨会话保留 |
| 复用用户日常 Chrome | `webExt: { disabled: true }` | 用户把 `.output/chrome-mv3-dev` 一次性 Load unpacked 进日常 Chrome（或按 [用户 Chrome 调试](${CLAUDE_PLUGIN_ROOT}/guides/extension/live-browser.md) 用扩展管理工具安装）；`npm run dev` 常驻后保存即自动整扩展重载，content script 更新需刷新宿主标签页；结束开发后移除或停用该 dev 扩展 |
| 专用持久 profile | `chromiumArgs: ['--user-data-dir=./.wxt/chrome-data']`（Windows 可用 `chromiumProfile` + `keepProfileChanges: true`） | 状态跨会话保留，适合固定测试账号 |

unpacked 扩展 ID 由目录路径派生，`.output/chrome-mv3-dev` 路径不变则 ID 稳定，重复加载等效更新。任何模式下都禁止把 `chromiumProfile` + `keepProfileChanges` 指向真实默认 user data dir：受单实例锁拦截，Chrome 136+ 禁用默认目录的调试管道，且有写坏 profile 风险。

## 3. 核对配置

- 全局 manifest 与 Vite 配置写入 `wxt.config.ts`，入口专属选项随入口声明；不手写生成的 `manifest.json`。
- 入口文件位于 `entrypoints/` 顶层或其直接子目录的 `index.*`；辅助文件放在对应入口目录内，避免被当作独立入口构建。
- 保留模板的 `dev` / `build` / `zip`、`compile`（`tsc --noEmit`）和 `postinstall`（`wxt prepare`）脚本。
- 确认 `.gitignore` 忽略 `.output/`、`.wxt/`、`node_modules/`。

## 4. 按需接入局部测试

先按 [testing.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/testing.md) 判断覆盖缺口。已有测试管线沿用；新工程只有出现真实浏览器/场景验证难稳定覆盖的重要规则时，才安装 `vitest` 并创建 `vitest.config.ts`：

```ts
import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing/vitest-plugin';

export default defineConfig({
  plugins: [WxtVitest()],
});
```

采用 Vitest 时新增 `test:run`（`vitest run`）脚本，用首个有实际业务断言的定向用例验证管线；不为证明框架可运行新增占位冒烟单测。没有局部测试需求时跳过接入，在初始化结果中说明，继续验证真实加载和构建。

## 5. 验证与衔接

按第 2 步选定的模式运行 `npm run dev`，确认扩展加载及模板页面正常（复用日常 Chrome 模式下由用户确认）后停止开发进程，再执行：

```bash
npm run compile
npm run build
```

已有受影响测试或本次新增高价值用例时，再执行对应的定向测试命令；没有测试管线不要求 `test:run`。按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 记录真实加载、模板交互和构建结果，必要运行结果尚未取得时初始化保持未完成。

构建后核对 `.output/chrome-mv3/manifest.json`：模板入口存在，权限未增加。后续功能变更的门禁按 [validation.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/validation.md)，允许使用项目等价脚本。

检查失败时修复对应配置并重跑，不重新生成工程。全部通过后完成初始化；需求来源齐备后进入 `/t-tools:t-design <feature>`，缺失时先补齐 PRD / 用户故事，纯技术方案按 [需求来源协议](${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md) 使用技术预研。

脚手架参数或框架行为不确定时查 [WXT init](https://wxt.dev/api/cli/wxt-init)、[入口](https://wxt.dev/guide/essentials/entrypoints) 和 [manifest 配置](https://wxt.dev/guide/essentials/config/manifest)。
