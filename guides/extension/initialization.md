# Chrome 扩展工程初始化

从零搭建符合 extension 技术基线（Chrome MV3 + WXT + React + TypeScript）的工程。`t-init` 不提供扩展模板，本页是其替代入口。已有 WXT 工程时直接进入 `t-design`，不重新初始化。

## 初始化步骤

### 1. 脚手架

```bash
npx wxt@latest init <目录名> -t react --pm <npm|pnpm|yarn|bun>
```

- 模板固定 `react`（Vanilla/Vue/Solid/Svelte 不在本基线）；所有模板默认 TypeScript，无需额外配置。
- 全栈仓库内目录名为 `extension/`（默认代码目录，见 [development.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/development.md)）；独立扩展项目用仓库根目录。验证命令一律在扩展实际目录内运行。
- `-t`/`--pm` 与位置参数目录名用于免交互执行；参数不全时 init 会进入交互提问。

### 2. 核对生成产物

- `wxt.config.ts` — manifest 与 Vite 配置的唯一入口；manifest 只写在这里，不手写 `manifest.json`。
- `entrypoints/`（入口，见下表）、`public/`（原样复制的静态文件，图标放这里）、`assets/`；`components/`、`hooks/`、`utils/` 按需创建，创建即自动导入。
- scripts 含 `dev` / `build` / `zip`，以及 `postinstall: wxt prepare`（生成 `.wxt/` 类型）。
- 确认 `.gitignore` 忽略 `.output/`、`.wxt/`、`node_modules`；前两者是派生物，不入库。

### 3. 对齐技术基线

依赖选型边界以 [development.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/development.md) 为准，初始化只做：

- 存储用 WXT 内置 storage（`wxt/utils/storage`），不安装 `@wxt-dev/storage`。
- `@webext-core/messaging`、`zod` 在设计需要消息协议或外部输入校验时安装；初始化阶段可先不引入。
- Tailwind/Radix、Zustand、TanStack Query 仅在设计采用时引入；无后端的扩展不引入 Query。
- permissions / host_permissions 保持模板默认；权限增量必须有设计依据，初始化阶段不添加。

### 4. 测试脚手架

- 安装 `vitest`（devDependency）；`wxt/testing` 随 WXT 提供，不安装 `wxt-vitest`。
- `vitest.config.ts` 接入 WxtVitest，复用 WXT 的 Vite 配置、自动导入与 fakeBrowser：

```ts
import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing/vitest-plugin';

export default defineConfig({
  plugins: [WxtVitest()],
});
```

- scripts 必须含 `test:run`（`vitest run`）与 `compile`（模板默认 `tsc --noEmit`）；[validation.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/validation.md) 以这两个脚本为门禁入口。
- 初始化只放一个冒烟单测确认测试管线可用；用例写法、fakeBrowser 与 MSW 边界读 [testing.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/testing.md)。

### 5. 入口与 manifest 事实

文件名决定入口类型；`entrypoints/` 内目录最多一层，入口的辅助文件放入口目录内，不散落在 `entrypoints/` 顶层（会被当作新入口构建）。

| 入口 | 文件形式 | 生成的 manifest 字段 |
|---|---|---|
| background | `entrypoints/background.ts` 或 `background/index.ts` | `background`（MV3 service worker） |
| popup | `entrypoints/popup/index.html` 或 `popup.html` | `action` |
| options | `entrypoints/options/index.html` 或 `options.html` | `options_ui` |
| content script | `entrypoints/<name>.content/index.tsx` 或 `<name>.content.ts` | `content_scripts` |
| side panel（按需） | `entrypoints/sidepanel/index.html` | `side_panel` |

- JS 入口的运行时代码放 `defineBackground` / `defineContentScript` 的 `main` 内：WXT 构建期会在 Node 中求值这些模块，顶层不能有 DOM 或 browser API 副作用。
- `name`、`version` 取自 `package.json`；权限与 `host_permissions` 写 `wxt.config.ts` 的 `manifest` 字段。构建产物 `.output/chrome-mv3/manifest.json` 是核对入口、权限与 CSP 的最终证据。
- 生成图标放 `public/`（如 `public/icon/16.png`）即可自动发现，不用手动声明 `manifest.icons`。

### 6. 验证并入库

```bash
npm run dev      # 启动开发模式，自动打开已加载扩展的浏览器
npm run compile  # 类型检查
npm run build    # 生产构建到 .output/chrome-mv3
```

- build 后核对 `.output/chrome-mv3/manifest.json`：入口齐全、权限不超出模板默认。dev 模式为热更新临时加入 `tabs`/`scripting` 权限，不算权限增量。
- 通过后提交初始工程，进入 `/t-tools:t-design <feature>` 开始功能设计。

## 边界

- 本页只覆盖从零建工程；开发实践、测试细节、完成前门禁与只读验收分属本目录 development / testing / validation / quality。
- Firefox 等其他浏览器目标（`-b firefox`）仅在产品要求时采用；默认基线是 Chrome MV3。

库级事实变更时核对 [WXT 安装指南](https://wxt.dev/guide/installation.html)、[wxt init CLI](https://wxt.dev/api/cli/wxt-init)、[目录结构](https://wxt.dev/guide/essentials/project-structure)、[入口](https://wxt.dev/guide/essentials/entrypoints)、[manifest 配置](https://wxt.dev/guide/essentials/config/manifest)、[单元测试](https://wxt.dev/guide/essentials/unit-testing) 和 [Chrome MV3 概览](https://developer.chrome.com/docs/extensions/develop)。
