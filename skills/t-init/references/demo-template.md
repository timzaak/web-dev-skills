# Web Demo 测试包模板

仅在 t-init --web-demo 时读取。保留项目已有配置并按真实环境适配，不复制业务登录、数据库、应用构建或启动默认值。使用前从项目说明取得 URL、身份与数据 fixture；未确认的缺口不写成默认实现。

## demo/package.json

```json
{
  "name": "project-web-demo",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "playwright test",
    "type-check": "tsc --noEmit",
    "lint": "eslint e2e/"
  }
}
```

依赖由当前项目锁文件与兼容版本确定：@playwright/test、typescript、ESLint 及适用 TypeScript parser、playwright-unified-logger。不在模板固定版本；生成时写入真实依赖并安装锁定。日志 fixture 的导入/API 按 `${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/unified-logger-package-template.md` 与包实际导出。

## demo/playwright.config.ts

```typescript
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: process.env.DEMO_BASE_URL,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
})
```

不写默认端口；真实故事运行前验证 DEMO_BASE_URL，项目已有 URL 配置时复用。由项目自行管理环境或 fixture 时 runner 使用 --no-auto-env。

## demo/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noEmit": true,
    "types": ["node"]
  },
  "include": ["e2e/**/*.ts", "playwright.config.ts"]
}
```

ESLint 使用项目兼容的配置并覆盖 demo/e2e/；.gitignore 仅忽略本包 node_modules、test-results、playwright-report 等生成物，不覆盖现有规则。

## demo/e2e/smoke.e2e.ts

```typescript
import { test, expect } from 'playwright-unified-logger/fixtures'

test('browser and logger smoke', async ({ page }) => {
  await page.setContent('<main><h1>Demo infrastructure ready</h1></main>')
  await expect(page.getByRole('heading')).toHaveText('Demo infrastructure ready')
})
```

smoke 仅验证浏览器与日志通路；导入路径先核对包实际 exports。实际故事、认证、数据准备与清理按项目需求另行设计，由 web-demo 阶段交付并 accept，不在初始化虚构。

## 完成检查

安装与锁文件、lint、type-check、独立 smoke 全通过；runner 生成独立 run 日志且截图/trace 设置可用；scripts/index.md 记录 URL、身份、环境与数据隔离方式。未配置的真实故事能力标明缺口。
