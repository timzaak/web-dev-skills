# extension-demo 模板

仅由扩展 Demo 初始化流程使用。先读 [扩展测试指南](${CLAUDE_PLUGIN_ROOT}/guides/extension/testing.md)，加载、请求隔离、生命周期和现场证据规则以该指南为准；本文件只定义初始化产物及适配方式。

## Demo 配置

新建 `demo/` 时用目标项目包管理器安装 `@playwright/test`、`typescript`、`@types/node` 和 `playwright-unified-logger`，保存兼容版本与锁文件；已有 Demo 沿用依赖，不盲目升级。`package.json` 使用 ESM，包含 `type-check: tsc --noEmit`。`tsconfig.json` 至少设置 ESNext target/module、Bundler moduleResolution、noEmit、strict、skipLibCheck、Node types，覆盖 `e2e/**/*.ts` 与 `playwright.config.ts`。`.gitignore` 忽略 node_modules、test-results 和 playwright-report。

新建 `demo/playwright.config.ts`：

```ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/extension/**/*.e2e.ts',
  forbidOnly: !!process.env.CI,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: 0,
  workers: 1,
  fullyParallel: false,
  outputDir: 'test-results/artifacts',
  reporter: [['list'], ['html', { open: 'never' }]],
  projects: [{ name: 'demo-fast', use: { headless: true } }],
})
```

已有配置时增量合并，保留 Web 用例的发现范围与行为。现有 runner 固定选 `demo-fast`：扩展用例必须由此 project 发现，其他 browser project 应排除 `**/extension/**`，不要只新增一个 runner 不会选择的 `extension` project。已有全局 webServer 或依赖 project 会在 `--no-auto-env` 下照常执行，需按实际项目拆分环境配置或 fixture，让独立扩展不触发 Web 服务；不修改现有 Web 测试的必要环境。

## 构建产物定位

生成 `demo/e2e/extension/extension-target.ts`，将 `{{EXTENSION_BUILD_DIR}}` 替换成相对目标项目根目录的真实构建目录（全栈常见 `extension/.output/chrome-mv3`，独立项目常见 `.output/chrome-mv3`）。不依赖执行命令的 cwd：

```ts
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// 与 scripts/index.md 中的构建命令保持一致。
export const extensionPath = path.resolve(
  fileURLToPath(new URL('../../../', import.meta.url)),
  '{{EXTENSION_BUILD_DIR}}',
)
```

每次执行前先运行项目实际 build，成功后才启动 runner。fixture 检查 manifest 存在不能证明构建新鲜度；构建命令、结果与产物路径一起记录在初始化结果和 `scripts/index.md`。

## 基础 fixture

生成 `demo/e2e/extension/fixtures.ts`，已有等价 fixture 则复用并补齐缺口：

```ts
import { chromium, test as base } from '@playwright/test'
import { createHash } from 'node:crypto'
import { mkdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import { UnifiedLogger } from 'playwright-unified-logger'
import { extensionPath } from './extension-target'

type ExtensionManifest = {
  manifest_version: number
  name: string
  version: string
  key?: string
  background?: { service_worker?: string }
  action?: { default_popup?: string }
  options_ui?: { page: string }
  options_page?: string
}

export const test = base.extend<{
  extensionManifest: ExtensionManifest
  extensionId: string
  extensionLogs: void
}>({
  extensionManifest: async ({}, use) => {
    // 缺失或无效构建直接失败，不通过 skip 隐藏加载错误。
    const manifest = JSON.parse(
      await readFile(path.join(extensionPath, 'manifest.json'), 'utf8'),
    ) as ExtensionManifest
    if (manifest.manifest_version !== 3) throw new Error('需要 Chrome MV3 构建产物')
    await use(manifest)
  },
  context: async ({ extensionManifest, headless }, use, testInfo) => {
    await testInfo.attach('extension-build', {
      body: Buffer.from(JSON.stringify({ path: extensionPath, manifest: extensionManifest })),
      contentType: 'application/json',
    })
    const context = await chromium.launchPersistentContext('', {
      channel: 'chromium',
      headless,
      args: [
        `--disable-extensions-except=${extensionPath}`,
        `--load-extension=${extensionPath}`,
      ],
    })
    try {
      await use(context)
    } finally {
      await context.close()
    }
  },
  extensionId: async ({ context, extensionManifest }, use) => {
    let id: string
    if (extensionManifest.background?.service_worker) {
      const isExtensionWorker = (url: string) => url.startsWith('chrome-extension://')
      const worker = context.serviceWorkers().find(w => isExtensionWorker(w.url()))
        ?? await context.waitForEvent('serviceworker', {
          predicate: w => isExtensionWorker(w.url()), timeout: 10_000,
        })
      id = new URL(worker.url()).host
    } else if (extensionManifest.key) {
      // Chromium 的公钥 ID 算法；只读取现有 key，不修改生产 manifest。
      id = createHash('sha256').update(Buffer.from(extensionManifest.key, 'base64'))
        .digest('hex').slice(0, 32)
        .replace(/[0-9a-f]/g, n => String.fromCharCode(97 + parseInt(n, 16)))
    } else {
      id = process.env.EXTENSION_ID ?? ''
    }
    if (!/^[a-p]{32}$/.test(id)) {
      throw new Error('没有可用扩展 ID；为无 background/key 的页面测试提供本次产物的 EXTENSION_ID')
    }
    await use(id)
  },
  extensionLogs: [async ({ page }, use) => {
    // 自动启用日志，失败时也落盘；page 来自上面的扩展 context。
    const outputDir = path.resolve(process.env.UNIFIED_LOG_OUTPUT_DIR
      || process.env.DEMO_LOG_OUTPUT_DIR || 'test-results/unified-logs')
    await mkdir(outputDir, { recursive: true })
    const logger = new UnifiedLogger(page, test.info().title, { outputDir })
    try {
      await use()
    } finally {
      await logger.finalize()
    }
  }, { auto: true }],
})

export const expect = test.expect
```

该 fixture 仅负责默认 page 的统一日志；故事涉及新页面、content script 或 worker 时按实际 API 增加对应日志采集，不能把 page 日志当作后台请求证据。手动创建的 context 不应被假定自动继承全部 `use` 配置；需要代理、证书、视频或 trace 时显式适配并验证。

没有 background 时不等待 worker。已有 manifest key 可用于确定 ID；无 key 的页面测试需从本次产物的实际加载结果取得 ID 后配置 `EXTENSION_ID`，不得填写网上示例 ID。纯 content script 的测试直接使用 context/page 与宿主 fixture，不请求 `extensionId`。无法确定 ID 且必须访问扩展页面时报告阻塞，不添加假的 background 或修改生产 key。进入页面后校验 `chrome.runtime.id` 与预期一致。

## 最小加载测试

生成 `demo/e2e/extension/verification/smoke.e2e.ts`，从实际入口选择一条最小可靠路径，不照搬网上示例的计数器、页面标题或网址：

- popup/options：读取 manifest 的实际页面路径，在扩展 URL 打开并核对 `chrome.runtime.id`，断言代码中真实存在的稳定 UI；已有可测交互时操作并核对持久状态或稳定页面结果。直接打开 popup URL 只证明页面路径，不宣称覆盖工具栏生命周期或 activeTab 授权。
- content script：fixture 启动与实际 matches/权限匹配的宿主页面，导航后断言真实注入效果；只在现有声明允许的站点/协议内运行，不为了测试扩大生产权限。没有合法可控宿主时先暴露缺口。
- 只有 background：从真实事件或既有消息入口触发一条现有行为，核对其可观察结果；不能仅靠 `serviceWorkers().length` 通过，不注入一套代替生产逻辑的测试 handler。

用例必须从 `../fixtures` 导入 `test/expect`，让所有页面都来自扩展 context。宿主/stub helper 在 teardown 中关闭服务并重置数据；后台请求使用真实 HTTP stub/测试后端，不能用 page.route 假装隔离成功。没有可测行为时说明阻塞，不编造成功用例。

## 官方依据

维护模板或目标锁定版本存在行为差异时读取：

- [WXT E2E 指南](https://wxt.dev/guide/essentials/e2e-testing.html) 与 [完整示例](https://github.com/wxt-dev/examples/tree/main/examples/playwright-e2e-testing)：先构建，再加载输出目录；示例版本不作为本仓库锁定版本。
- [Playwright Chrome extensions](https://playwright.dev/docs/chrome-extensions)：Chromium persistent context、fixture 与扩展页面。
- [Chrome 端到端测试](https://developer.chrome.com/docs/extensions/how-to/test/end-to-end-testing)：用户可观察结果、popup 页面与真实弹窗的差异。
- [Manifest key](https://developer.chrome.com/docs/extensions/reference/manifest/key) 与 [Chromium ID 实现](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/crx_file/id_util.cc)：现有公钥的确定性 ID。
