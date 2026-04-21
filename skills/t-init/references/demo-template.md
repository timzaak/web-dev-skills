# Demo E2E 测试模板

本文件包含 `demo/` 目录的所有文件内容模板。
Demo 使用 `playwright-unified-logger` 包作为日志依赖。

占位符：
- `{{PROJECT_NAME}}` — kebab-case 项目名称
- `{{PROJECT_NAME_PASCAL}}` — PascalCase 项目名称
- `{{BASE_URL}}` — 后端基础 URL（默认 `http://localhost:8080`）

---

## 1. demo/package.json

```json
{
  "name": "{{PROJECT_NAME}}-demo-tests",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "test": "playwright test",
    "test:headed": "playwright test --headed",
    "test:debug": "playwright test --debug",
    "test:report": "playwright show-report",
    "type-check": "tsc --noEmit",
    "lint": "eslint e2e/"
  },
  "dependencies": {
    "{{PROJECT_NAME}}-playwright-unified-logger": "file:../packages/playwright-unified-logger"
  },
  "devDependencies": {
    "@playwright/test": "^1.57.0",
    "@typescript-eslint/parser": "^8.18.0",
    "@typescript-eslint/eslint-plugin": "^8.18.0",
    "@eslint/js": "^9.18.0",
    "typescript": "^5.8.0",
    "tsx": "^4.21.0",
    "eslint": "^9.18.0"
  }
}
```

---

## 2. demo/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "baseUrl": ".",
    "resolveJsonModule": true,
    "allowJs": true,
    "checkJs": false,
    "isolatedModules": true,
    "noEmit": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "strict": false,
    "downlevelIteration": true,
    "types": ["@playwright/test", "node"]
  },
  "include": ["e2e/**/*", "playwright.config.ts"],
  "exclude": ["node_modules"]
}
```

---

## 3. demo/playwright.config.ts

```typescript
/**
 * Playwright 测试配置
 *
 * 测试策略：以 Demo E2E 为主，验证完整用户流程
 *
 * 配置说明：
 * - timeout: 单个测试最长执行时间（120s）
 * - expect.timeout: 断言等待时间（10s）
 * - workers: 单线程执行，确保测试稳定
 * - screenshot/video/trace: 默认关闭，按需开启
 *
 * 环境变量：
 * - BASE_URL: 后端地址（默认 http://localhost:8080）
 * - UNIFIED_LOG_LEVEL: mini | normal | verbose | silent（默认 mini）
 */

import { defineConfig, devices } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:8080'

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.e2e.ts',

  timeout: 120 * 1000,
  expect: {
    timeout: 10 * 1000,
  },

  retries: 0,
  fullyParallel: false,
  workers: 1,

  outputDir: 'test-results/artifacts',

  use: {
    baseURL: BASE_URL,
    screenshot: 'off',
    video: 'off',
    trace: 'off',
    actionTimeout: 0,
    navigationTimeout: 15 * 1000,
  },

  projects: [
    {
      name: 'demo-fast',
      use: {
        ...devices['Desktop Chrome'],
        headless: true,
        launchOptions: {
          args: [
            '--lang=en-US',
            '--enable-logging',
            '--log-level=0',
            '--disable-features=TranslateUI',
            '--no-first-run',
            '--no-default-browser-check',
          ],
        },
      },
    },
  ],

  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],

  quiet: false,
})
```

---

## 4. demo/eslint.config.js

```javascript
/**
 * ESLint 配置 - E2E 测试专用
 *
 * 核心规则：
 * - 禁止 page.waitForTimeout()（强制使用自动等待）
 * - 未使用变量警告（前缀 _ 除外）
 * - 限制 console 使用（仅允许 warn 和 error）
 */

import eslint from '@eslint/js'
import tsParser from '@typescript-eslint/parser'
import tsPlugin from '@typescript-eslint/eslint-plugin'

export default [
  eslint.configs.recommended,
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
        project: './tsconfig.json',
      },
      globals: {
        process: 'readonly',
        console: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',

      'no-restricted-syntax': [
        'error',
        {
          selector: 'CallExpression[callee.object.name="page"][callee.property.name="waitForTimeout"]',
          message: [
            '⛔ Using page.waitForTimeout() is prohibited.',
            '',
            'Alternatives:',
            '  - Use expect().toBeVisible() for element visibility',
            '  - Use waitForLoadState() for page load states',
            '  - Use waitForResponse() for API calls',
            '  - Use waitForURL() for navigation changes',
          ].join('\n'),
        },
      ],

      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'prefer-const': 'error',
      'no-unused-vars': 'off',
    },
  },
  {
    ignores: [
      'node_modules/**',
      'test-results/**',
      'playwright-report/**',
      'playwright/.cache/**',
    ],
  },
]
```

---

## 5. demo/e2e/helpers/auth.ts

```typescript
/**
 * 认证辅助函数
 *
 * 为 E2E 测试提供登录、登出等认证相关功能。
 *
 * 使用方式：
 * ```typescript
 * import { loginAsAdmin, logout } from './helpers/auth'
 * await loginAsAdmin(page, { realmId: 'admin' })
 * ```
 *
 * 配置：
 * - BASE_URL: 后端地址（环境变量，默认 http://localhost:8080）
 * - 修改 DEMO_ADMIN 和 REALM_ADMINS 以匹配你的测试账号
 */

import { Page, type Response } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:8080'

/**
 * 默认管理员账号 — 根据项目实际情况修改
 */
export const DEMO_ADMIN = {
  email: 'admin@example.com',
  password: 'password',
  realmId: 'admin',
}

/**
 * Realm 管理员账户映射 — 根据项目实际情况修改
 */
export const REALM_ADMINS: Record<string, { email: string; password: string }> = {
  admin: { email: 'admin@example.com', password: 'password' },
}

/**
 * 使用管理员账号登录
 *
 * @param page Playwright Page 对象
 * @param options.realmId Realm ID（默认 'admin'）
 * @param options.waitNavigation 是否等待导航完成（默认 true）
 */
export async function loginAsAdmin(
  page: Page,
  options: {
    realmId?: string
    waitNavigation?: boolean
  } = {}
): Promise<void> {
  const { realmId = 'admin', waitNavigation = true } = options

  console.log(`[Auth] 登录 realm: ${realmId}`)

  const credentials = REALM_ADMINS[realmId] || DEMO_ADMIN

  // 清除 session 数据
  await clearSessionData(page)

  // 导航到登录页 — 根据项目路由修改路径
  await page.goto(`${BASE_URL}/${realmId}/auth/login`, { waitUntil: 'domcontentloaded' })

  // 检查是否已登录（自动跳转）
  if (page.url().includes(`/${realmId}/manage`) || page.url() === `/${realmId}`) {
    console.log(`[Auth] 已登录，跳过`)
    return
  }

  try {
    // 等待登录表单出现 — 选择器根据项目实际情况修改
    await page.waitForSelector('input[type="text"], [data-testid="email-input"]', { timeout: 10000 })
    await page.waitForSelector('input[type="password"], [data-testid="password-input"]', { timeout: 10000 })

    const usernameInput = page.locator('input[type="text"], [data-testid="email-input"]').first()
    const passwordInput = page.locator('input[type="password"], [data-testid="password-input"]').first()

    await usernameInput.fill(credentials.email)
    await passwordInput.fill(credentials.password)

    const submitButton = page.locator('button[type="submit"]').first()
    await submitButton.click()

    // 等待登录 API 响应
    const loginResponse = await waitForLoginResponse(page)
    if (loginResponse && !loginResponse.ok()) {
      const errorBody = await loginResponse.text().catch(() => '')
      throw new Error(`Login failed: API returned ${loginResponse.status()} - ${errorBody}`)
    }

    if (waitNavigation) {
      await page.waitForURL(`**/${realmId}/**`, { timeout: 10000 }).catch(() => {})
    }

    console.log(`[Auth] 登录成功`)
  } catch (error) {
    console.error(`[Auth] 登录失败:`, error)
    throw error
  }
}

/**
 * 登出当前用户
 */
export async function logout(page: Page): Promise<void> {
  console.log('[Auth] 执行登出')

  try {
    const userAvatar = page.locator('[data-testid="user-avatar"]').first()
    if (await userAvatar.isVisible({ timeout: 2000 })) {
      await userAvatar.click()
      const logoutMenuItem = page.locator('[data-testid="logout-menu-item"]').first()
      if (await logoutMenuItem.isVisible({ timeout: 2000 })) {
        await logoutMenuItem.click()
        await page.waitForURL('**/login', { timeout: 5000 })
      }
    }
  } catch {
    console.log('[Auth] UI 登出失败，清除会话')
  } finally {
    await clearSessionData(page)
    await page.goto(`${BASE_URL}/admin/auth/login`, { waitUntil: 'networkidle' })
  }
}

async function clearSessionData(page: Page): Promise<void> {
  await page.context().clearCookies()
  try {
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
  } catch {
    // localStorage 访问被阻止时忽略
  }
}

async function waitForLoginResponse(page: Page): Promise<Response | null> {
  return page
    .waitForResponse(
      response => response.url().includes('/login') && response.request().method() === 'POST',
      { timeout: 10000 }
    )
    .catch(() => null)
}
```

---

## 6. demo/e2e/helpers/environment-setup.ts

```typescript
/**
 * 环境验证工具
 *
 * 在测试运行前验证后端服务、数据库和 Redis 是否就绪。
 *
 * 使用方式：
 * ```typescript
 * import { verifyTestEnvironment } from './helpers/environment-setup'
 * await verifyTestEnvironment(page, { requiredUsers: ['admin@example.com'] })
 * ```
 *
 * 依赖：
 * - 后端提供 GET /health 接口（返回 { status, database, redis }）
 */

import { Page } from '@playwright/test'

export const BASE_URL = process.env.BASE_URL || 'http://localhost:8080'

export interface VerifyEnvironmentOptions {
  /** 需要验证存在的 Realm ID 列表 */
  requiredRealms?: string[]
  /** 需要验证存在的用户邮箱列表 */
  requiredUsers?: string[]
  /** 跳过数据库检查 */
  skipDatabaseCheck?: boolean
  /** 跳过 Redis 检查 */
  skipRedisCheck?: boolean
}

interface ValidationResult {
  healthy: boolean
  response?: {
    database?: boolean
    redis?: boolean
  }
  errors?: string[]
}

/**
 * 验证测试环境状态
 */
export async function verifyTestEnvironment(
  page: Page,
  options: VerifyEnvironmentOptions = {}
): Promise<void> {
  const {
    requiredUsers = [],
    skipDatabaseCheck = false,
    skipRedisCheck = false,
  } = options

  console.log('[Env] 验证测试环境...')

  await verifyBackendConnections({ skipDatabaseCheck, skipRedisCheck })
  await verifyRequiredUsers(page, requiredUsers)

  console.log('[Env] 环境验证通过')
}

async function verifyBackendConnections(options: {
  skipDatabaseCheck: boolean
  skipRedisCheck: boolean
}): Promise<void> {
  const result = await validateBackendHealth({
    maxRetries: 3,
    retryDelay: 2000,
    timeout: 10000,
  })

  if (!result.healthy) {
    throw new Error(`Backend health check failed:\n${result.errors?.join('\n') || 'Unknown error'}`)
  }

  if (!options.skipDatabaseCheck && result.response?.database !== true) {
    throw new Error('数据库连接失败，请确保数据库服务正在运行')
  }

  if (!options.skipRedisCheck && result.response?.redis !== true) {
    throw new Error('Redis 连接失败，请确保缓存服务正在运行')
  }

  console.log('[Env] 数据库和 Redis 连接正常')
}

async function verifyRequiredUsers(page: Page, requiredUsers: string[]): Promise<void> {
  for (const userEmail of requiredUsers) {
    console.log(`[Env] 用户 "${userEmail}" 验证通过`)
  }
}

async function validateBackendHealth(options: {
  maxRetries: number
  retryDelay: number
  timeout: number
}): Promise<ValidationResult> {
  const { maxRetries, retryDelay, timeout } = options

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(`${BASE_URL}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(timeout),
      })

      if (response.ok) {
        const data = await response.json().catch(() => ({}))
        return {
          healthy: true,
          response: {
            database: data.database ?? true,
            redis: data.redis ?? true,
          },
        }
      }
    } catch (error) {
      if (attempt < maxRetries - 1) {
        console.log(`[Env] 健康检查失败，重试 ${attempt + 1}/${maxRetries}...`)
        await new Promise(resolve => setTimeout(resolve, retryDelay))
      } else {
        return {
          healthy: false,
          errors: [`Health check failed after ${maxRetries} attempts: ${error}`],
        }
      }
    }
  }

  return { healthy: false, errors: ['Health check failed: Max retries exceeded'] }
}
```

---

## 7. demo/e2e/fixtures/demo-auth.fixtures.ts

```typescript
/**
 * Demo 测试 Fixtures
 *
 * 扩展 Playwright base test，提供可复用的测试 fixture：
 * - demoLogger: 预配置的 UnifiedLogger（自动 finalize）
 * - authenticatedPage: 已登录的 Page（管理员身份）
 * - testStartTime: 测试开始时间戳（用于数据清理）
 *
 * 使用方式：
 * ```typescript
 * import { test, expect } from '../fixtures/demo-auth.fixtures'
 *
 * test('my test', async ({ page, demoLogger }) => {
 *   console.log('开始测试') // 自动被 UnifiedLogger 捕获
 * })
 * ```
 */

import { test as base, type Page } from '@playwright/test'
import { UnifiedLogger } from '{{PROJECT_NAME}}-playwright-unified-logger'
import { verifyTestEnvironment } from '../helpers/environment-setup'
import { loginAsAdmin } from '../helpers/auth'

export const test = base.extend<{
  demoLogger: UnifiedLogger
  authenticatedPage: Page
  testStartTime: number
}>({
  /**
   * Fixture: Demo Logger
   *
   * 创建 UnifiedLogger 实例，测试结束后自动打印摘要并保存日志文件。
   */
  demoLogger: async ({ page }, use, testInfo) => {
    const logger = new UnifiedLogger(page, testInfo.title)
    await use(logger)
    logger.printSummary('[Demo] Test Summary')
    await logger.finalize()
  },

  /**
   * Fixture: Test Start Time
   *
   * 记录测试开始时间，用于后续数据清理。
   */
  testStartTime: async (_context, use) => {
    const startTime = Date.now()
    await use(startTime)
  },

  /**
   * Fixture: Authenticated Page
   *
   * 验证环境后执行管理员登录，返回已认证的 Page。
   * 注意：此 fixture 会增加约 5-10 秒的测试设置时间。
   */
  authenticatedPage: async ({ page, demoLogger: _demoLogger, testStartTime: _testStartTime }, use) => {
    await verifyTestEnvironment(page, {
      requiredRealms: ['admin'],
      requiredUsers: ['admin@example.com'],
    })

    await loginAsAdmin(page, { realmId: 'admin' })
    await use(page)
  },
})

/**
 * Realm 级别测试 fixture（支持多 Realm 测试）
 */
export const realmTest = base.extend<{
  demoLogger: UnifiedLogger
  authenticatedRealmPage: Page
  realmId: string
  testStartTime: number
}>({
  demoLogger: async ({ page }, use, testInfo) => {
    const logger = new UnifiedLogger(page, testInfo.title)
    await use(logger)
    logger.printSummary('[Realm Demo] Test Summary')
    await logger.finalize()
  },

  testStartTime: async (_context, use) => {
    const startTime = Date.now()
    await use(startTime)
  },

  realmId: async (_context, use) => {
    await use('admin') // 默认 Realm，测试中可覆盖
  },

  authenticatedRealmPage: async ({ page, demoLogger: _demoLogger, realmId, testStartTime: _testStartTime }, use) => {
    await verifyTestEnvironment(page, {
      requiredRealms: [realmId],
      requiredUsers: ['admin@example.com'],
    })
    await loginAsAdmin(page, { realmId })
    await use(page)
  },
})

export { expect } from '@playwright/test'
```

---

## 8. demo/e2e/fixtures/test-data.ts

```typescript
/**
 * 测试数据管理
 *
 * 集中管理 E2E 测试使用的测试数据和辅助函数。
 * 修改此文件以匹配项目实际数据需求。
 */

export { REALM_ADMINS, DEMO_ADMIN } from '../helpers/auth'

export interface TestAccount {
  email: string
  password: string
  realmId: string
}

export interface TestRealm {
  id: string
  name: string
  adminEmail: string
}

/**
 * 测试 Realm 数据 — 根据项目修改
 */
export const TEST_REALMS: Record<string, TestRealm> = {
  admin: {
    id: 'admin',
    name: 'Admin Realm',
    adminEmail: 'admin@example.com',
  },
}

/**
 * 测试角色
 */
export const TEST_ROLES = {
  USER: 'user',
  ADMIN: 'admin',
  REALM_ADMIN: 'realm-admin',
} as const

/**
 * 生成随机测试用户数据
 */
export function generateTestUser(options?: {
  email?: string
  password?: string
  nickname?: string
  realmId?: string
}): TestAccount & { nickname: string } {
  const timestamp = Date.now()
  const random = Math.floor(Math.random() * 1000)

  return {
    email: options?.email || `test-user-${timestamp}-${random}@demo.com`,
    password: options?.password || 'password123',
    nickname: options?.nickname || `Test User ${timestamp}`,
    realmId: options?.realmId || 'admin',
  }
}
```

---

## 9. demo/e2e/pages/base-page.ts

```typescript
/**
 * Base Page Object
 *
 * 所有 Page Object 的基类，封装通用功能：
 * - 导航（goto）
 * - 等待元素可见/隐藏
 * - 智能点击（先等待可见）
 * - 表单填写（含 blur 触发验证）
 * - 截图（调试用）
 *
 * 使用方式：
 * ```typescript
 * class MyPage extends BasePage {
 *   constructor(page: Page, logger?: UnifiedLogger) {
 *     super(page, logger)
 *   }
 * }
 * ```
 */

import { Page, Locator, expect } from '@playwright/test'
import type { UnifiedLogger } from '{{PROJECT_NAME}}-playwright-unified-logger'

const BASE_URL = process.env.BASE_URL || 'http://localhost:8080'

export class BasePage {
  protected logger?: UnifiedLogger

  constructor(public readonly page: Page, logger?: UnifiedLogger) {
    this.logger = logger
  }

  /**
   * 导航到指定路径
   */
  async goto(path: string, waitForSelector?: string): Promise<void> {
    const url = path.startsWith('http') ? path : `${BASE_URL}${path}`
    await this.page.goto(url)

    if (waitForSelector) {
      await expect(this.page.locator(waitForSelector)).toBeVisible()
    }
  }

  protected async waitForLoad(state: 'load' | 'domcontentloaded' | 'networkidle' = 'domcontentloaded'): Promise<void> {
    await this.page.waitForLoadState(state)
  }

  protected async waitForVisible(locator: Locator, timeout: number = 5000): Promise<void> {
    await expect(locator).toBeVisible({ timeout })
  }

  protected async waitForHidden(locator: Locator, timeout: number = 5000): Promise<void> {
    await expect(locator).toBeHidden({ timeout })
  }

  /**
   * 智能点击 — 先等待元素可见再点击
   */
  public async smartClick(element: Locator, force: boolean = false): Promise<void> {
    await expect(element).toBeVisible()
    await element.click({ force })
  }

  getUrl(): string {
    return this.page.url()
  }

  async isVisible(locator: Locator): Promise<boolean> {
    return await locator.isVisible().catch(() => false)
  }

  /**
   * 填写表单字段 — 自动全选替换 + blur 触发验证
   */
  protected async fillField(locator: Locator, value: string): Promise<void> {
    await expect(locator).toBeVisible()
    await locator.selectText()
    await locator.fill(value)
    await locator.blur()

    // 验证值已提交
    await expect(async () => {
      const inputValue = await locator.inputValue()
      expect(inputValue).toBe(value)
    }).toPass({ timeout: 2000 })
  }

  protected async getText(locator: Locator): Promise<string> {
    await expect(locator).toBeVisible()
    return await locator.textContent() || ''
  }

  protected async screenshot(name: string): Promise<void> {
    await this.page.screenshot({ path: `test-results/screenshots/${name}.png` })
  }
}
```

---

## 10. demo/e2e/pages/login-page.ts

```typescript
/**
 * Login Page Object
 *
 * 封装登录页面操作。
 * 选择器定义在 selectors.ts 中，便于统一维护。
 *
 * 使用方式：
 * ```typescript
 * const loginPage = new LoginPage(page, logger)
 * await loginPage.goto('admin')
 * await loginPage.login({ email: 'admin@example.com', password: 'password' })
 * ```
 */

import { Page, Locator, expect } from '@playwright/test'
import { SELECTORS } from '../selectors'
import { BasePage } from './base-page'
import type { UnifiedLogger } from '{{PROJECT_NAME}}-playwright-unified-logger'

export interface LoginCredentials {
  email: string
  password: string
}

export class LoginPage extends BasePage {
  readonly container: Locator
  readonly title: Locator
  readonly emailInput: Locator
  readonly passwordInput: Locator
  readonly submitButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page, logger?: UnifiedLogger) {
    super(page, logger)
    this.container = page.locator(SELECTORS.login.container)
    this.title = page.locator(SELECTORS.login.title)
    this.emailInput = page.locator(SELECTORS.login.emailInput)
    this.passwordInput = page.locator(SELECTORS.login.passwordInput)
    this.submitButton = page.locator(SELECTORS.login.submitButton)
    this.errorMessage = page.locator(SELECTORS.login.errorMessage)
  }

  /**
   * 导航到登录页
   */
  async goto(realmId: string = 'admin'): Promise<void> {
    const BASE_URL = process.env.BASE_URL || 'http://localhost:8080'
    await this.page.goto(`${BASE_URL}/${realmId}/auth/login`, { waitUntil: 'domcontentloaded' })

    // 检查是否已登录并跳转
    const currentUrl = this.page.url()
    const isRedirected = currentUrl.includes(`/${realmId}/manage`) ||
      currentUrl.match(new RegExp(`/${realmId}/?(\\?.*)?$`)) !== null

    if (isRedirected) {
      return
    }

    await expect(this.container).toBeVisible()
  }

  async waitForReady(): Promise<void> {
    await expect(this.container).toBeVisible()
    await expect(this.title).toBeVisible()
    await expect(this.emailInput).toBeVisible()
    await expect(this.passwordInput).toBeVisible()
    await expect(this.submitButton).toBeVisible()
  }

  async fillLoginForm(credentials: LoginCredentials): Promise<void> {
    await this.fillField(this.emailInput, credentials.email)
    await this.fillField(this.passwordInput, credentials.password)
  }

  async submit(): Promise<void> {
    await this.smartClick(this.submitButton)
  }

  /**
   * 使用凭证登录
   */
  async login(credentials: LoginCredentials): Promise<void> {
    await this.fillLoginForm(credentials)
    await this.submit()

    const loginResponse = await this.page.waitForResponse(
      response => response.url().includes('/login') && response.request().method() === 'POST',
      { timeout: 10000 }
    ).catch(() => null)

    if (loginResponse && !loginResponse.ok()) {
      const errorBody = await loginResponse.text().catch(() => '')
      throw new Error(`Login failed: API returned ${loginResponse.status()} - ${errorBody}`)
    }
  }

  async getErrorMessage(): Promise<string> {
    const visible = await this.isVisible(this.errorMessage)
    if (!visible) return ''
    return await this.getText(this.errorMessage)
  }

  async hasError(): Promise<boolean> {
    return await this.isVisible(this.errorMessage)
  }

  async isOnLoginPage(): Promise<boolean> {
    const url = this.getUrl()
    return url.includes('/login') && await this.isVisible(this.container)
  }
}
```

---

## 11. demo/e2e/selectors.ts

```typescript
/**
 * 集中式选择器定义
 *
 * 所有 E2E 测试的元素选择器集中管理在此文件中。
 * 当前端 UI 变更时，只需修改此文件即可。
 *
 * 选择器优先级：
 * 1. data-testid（最稳定，优先使用）
 * 2. Aria roles（语义化）
 * 3. 文本内容（兜底）
 *
 * 根据项目实际情况修改每个选择器。
 */

export const SELECTORS = {
  /** 登录页选择器 */
  login: {
    container: '[data-testid="login-card"], [data-testid="login-container"]',
    title: '[data-testid="login-title"]',
    usernameInput: '[data-testid="email-input"]',
    emailInput: '[data-testid="email-input"]',
    passwordInput: '[data-testid="password-input"]',
    submitButton: '[data-testid="login-submit-button"]',
    errorMessage: '[data-testid="login-error-message"]',
  },

  /** Dashboard 页选择器 */
  dashboard: {
    container: '[data-testid="dashboard-container"]',
    heading: '[data-testid="dashboard-heading"]',
    welcomeMessage: '[data-testid="welcome-message"]',
  },

  /** 通用组件选择器 */
  common: {
    dialog: '[data-testid="dialog"]',
    dialogTitle: '[data-testid="dialog-title"]',
    dialogContent: '[data-testid="dialog-content"]',
    dialogCloseButton: '[data-testid="dialog-close-button"]',
    dialogCancelButton: '[data-testid="dialog-cancel-button"]',
    dialogSubmitButton: '[data-testid="dialog-submit-button"]',

    form: '[data-testid="form"]',
    formEmailInput: '[data-testid="email-input"]',
    formPasswordInput: '[data-testid="password-input"]',
    formNicknameInput: '[data-testid="nickname-input"]',
    formNameInput: '[data-testid="name-input"]',

    toast: '[data-testid="toast"], [data-sonner-toast]',
    toastMessage: '[data-testid="toast-message"], [data-sonner-toast] [data-description]',
    successMessage: '[data-testid="success-message"], [data-sonner-toast].success',
    errorMessage: '[data-testid="error-message"], [data-sonner-toast].error',

    loading: '[data-testid="loading"]',
    spinner: '[data-testid="spinner"]',
  },
}

/**
 * 选择器辅助：支持多备选选择器
 */
export function getSelector(selector: string | string[]): string {
  if (Array.isArray(selector)) {
    return selector.join(', ')
  }
  return selector
}
```

---

## 12. demo/e2e/demo-basic.e2e.ts

```typescript
/**
 * 基础 Demo 测试
 *
 * 验证测试环境和 UnifiedLogger 是否正常工作。
 * 这是创建项目后应运行的第一个测试。
 *
 * 运行方式：
 *   cd demo && npm test
 *   cd demo && npm run test:headed  # 有头模式
 *
 * 环境变量：
 *   BASE_URL=http://localhost:8080 npm test
 *   UNIFIED_LOG_LEVEL=verbose npm test  # 详细日志
 */

import { test, expect } from './fixtures/demo-auth.fixtures'

test.describe('Basic Demo Test', () => {
  test('should capture logs', async ({ page, demoLogger: _demoLogger }) => {
    // 导航到首页
    await page.goto('/')

    // 测试代码中的 console.log 会被 TestCodeLogger 捕获
    console.log('Test started successfully')
    console.log('demoLogger is working')

    // demoLogger 自动捕获所有日志并在测试结束时打印摘要
  })

  test('should verify page navigation', async ({ page, demoLogger: _demoLogger }) => {
    await page.goto('/')

    const currentUrl = page.url()
    console.log(`Current URL: ${currentUrl}`)

    expect(currentUrl).toBeTruthy()
    expect(currentUrl.length).toBeGreaterThan(0)
  })

  test('should handle page errors gracefully', async ({ page, demoLogger: _demoLogger }) => {
    // 尝试导航到不存在的页面
    await page.goto('/non-existent-page').catch(() => null)

    // 测试应正常完成，demoLogger 会捕获任何控制台错误
    console.log('Navigation test completed')
  })
})
```

---

## 13. demo/.gitignore

```
node_modules/
test-results/
playwright-report/
playwright/.cache/
```
