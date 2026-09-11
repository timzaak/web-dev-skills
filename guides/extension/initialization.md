# Chrome 扩展工程初始化

从零搭建 WXT 工程时使用；`t-init` 尚无扩展模板。已有工程跳过初始化，后续按需求来源进入设计与任务阶段。

## 1. 创建工程

```bash
npx wxt@latest init <目录名> -t react --pm <npm|pnpm|yarn|bun>
```

- 全栈仓库默认放在 `extension/`，独立扩展以生成目录为仓库根目录；进入该目录，用选定的包管理器安装依赖。下文命令以 npm 为例。
- 技术基线按 [development.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/development.md)；初始化保留 React + TypeScript 模板，功能依赖与权限增量待设计明确后引入。

## 2. 核对配置

- 全局 manifest 与 Vite 配置写入 `wxt.config.ts`，入口专属选项随入口声明；不手写生成的 `manifest.json`。
- 入口文件位于 `entrypoints/` 顶层或其直接子目录的 `index.*`；辅助文件放在对应入口目录内，避免被当作独立入口构建。
- 保留模板的 `dev` / `build` / `zip`、`compile`（`tsc --noEmit`）和 `postinstall`（`wxt prepare`）脚本。
- 确认 `.gitignore` 忽略 `.output/`、`.wxt/`、`node_modules/`。

## 3. 接入测试

安装 `vitest` 为开发依赖，创建 `vitest.config.ts`：

```ts
import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing/vitest-plugin';

export default defineConfig({
  plugins: [WxtVitest()],
});
```

新增 `test:run`（`vitest run`）脚本和一个冒烟单测，验证测试管线可用；用例与 mock 边界按 [testing.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/testing.md)。

## 4. 验证与衔接

运行 `npm run dev`，确认扩展加载及模板页面正常后停止开发进程，再执行：

```bash
npm run compile
npm run test:run
npm run build
```

构建后核对 `.output/chrome-mv3/manifest.json`：模板入口存在，权限未增加。后续功能变更的门禁按 [validation.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/validation.md)，允许使用项目等价脚本。

检查失败时修复对应配置并重跑，不重新生成工程。全部通过后完成初始化；需求来源齐备后进入 `/t-tools:t-design <feature>`，缺失时先补齐 PRD / 用户故事，纯技术方案按 [需求来源协议](${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md) 使用技术预研。

脚手架参数或框架行为不确定时查 [WXT init](https://wxt.dev/api/cli/wxt-init)、[入口](https://wxt.dev/guide/essentials/entrypoints) 和 [manifest 配置](https://wxt.dev/guide/essentials/config/manifest)。
