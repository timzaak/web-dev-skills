# Playwright Unified Logger 包模板

本文件包含 `packages/playwright-unified-logger/` 独立 npm 包的所有文件内容模板。
这是一个通用的 Playwright E2E 测试日志库，可独立发布到 npm。

占位符：`{{PROJECT_NAME}}` (kebab-case)

---

## 1. packages/playwright-unified-logger/package.json

```json
{
  "name": "{{PROJECT_NAME}}-playwright-unified-logger",
  "version": "0.1.0",
  "description": "Unified logger for Playwright E2E tests - captures network, console, route changes and test code logs",
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "scripts": {
    "build": "tsc",
    "type-check": "tsc --noEmit",
    "prepublishOnly": "npm run build"
  },
  "peerDependencies": {
    "@playwright/test": ">=1.40.0"
  },
  "devDependencies": {
    "@playwright/test": "^1.57.0",
    "typescript": "^5.8.0"
  },
  "files": [
    "dist/",
    "src/"
  ],
  "keywords": [
    "playwright",
    "testing",
    "logging",
    "e2e",
    "network-logger",
    "console-logger"
  ],
  "license": "MIT"
}
```

---

## 2. packages/playwright-unified-logger/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": false
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

---

## 3. packages/playwright-unified-logger/src/index.ts

```typescript
/**
 * Playwright Unified Logger - 主入口
 *
 * 导出所有日志组件，供外部使用。
 *
 * 用法：
 * ```typescript
 * import { UnifiedLogger } from '{{PROJECT_NAME}}-playwright-unified-logger'
 *
 * const logger = new UnifiedLogger(page, 'my-test')
 * // ... 测试逻辑 ...
 * logger.printSummary('Test Summary')
 * await logger.finalize()
 * ```
 */

// 核心类
export { UnifiedLogger } from './unified-logger'
export type { TestLogs } from './unified-logger'

// 子日志器（可单独使用）
export { NetworkLogger } from './network-logger'
export type { ApiRequestLog } from './network-logger'

export { ConsoleLogger } from './console-logger'
export type { ConsoleLogEntry } from './console-logger'

export { RouteLogger } from './route-logger'
export type { RouteChangeLog } from './route-logger'

export { TestCodeLogger } from './test-code-logger'
export type { TestCodeLogEntry } from './test-code-logger'

// 配置
export {
  getLoggerConfig,
  isSilentMode,
  isVerboseMode,
  isMiniMode,
  formatLogPath,
} from './log-config'
export type { LoggerConfig, LogLevel } from './log-config'
```

---

## 4. packages/playwright-unified-logger/src/log-config.ts

```typescript
/**
 * Logger Configuration
 *
 * 环境变量控制日志行为，所有变量以 UNIFIED_LOG_ 为前缀。
 *
 * 环境变量：
 * - UNIFIED_LOG_LEVEL: mini | normal | verbose | silent (默认: mini)
 * - UNIFIED_LOG_DEDUP: true | false (默认: true) - 启用日志去重
 * - UNIFIED_LOG_AGGREGATE: true | false (默认: true) - 启用请求聚合
 * - UNIFIED_LOG_TEST_CODE: true | false (默认: true) - 启用测试代码日志
 * - UNIFIED_LOG_COMPACT: true | false (默认: false) - 极简输出模式
 */

import * as path from 'path'

export type LogLevel = 'mini' | 'normal' | 'verbose' | 'silent'

export interface LoggerConfig {
  /** 是否静默模式（减少控制台输出） */
  quietMode: boolean
  /** 是否启用日志去重 */
  deduplicationEnabled: boolean
  /** 当前日志级别 */
  logLevel: LogLevel
  /** 是否聚合相似请求 */
  aggregateLogs: boolean
  /** 是否记录测试代码日志 */
  testCodeLoggingEnabled: boolean
  /** 是否极简输出（单行） */
  compactMode: boolean
}

/**
 * 从环境变量获取日志配置
 *
 * 支持两种前缀（兼容旧版和新版）：
 * - UNIFIED_LOG_* （推荐）
 * - DEMO_LOG_* （向后兼容）
 */
export function getLoggerConfig(): LoggerConfig {
  const env = (key: string, fallback: string): string =>
    process.env[key] || fallback

  const logLevel = (env('UNIFIED_LOG_LEVEL', env('DEMO_LOG_LEVEL', 'mini'))) as LogLevel
  const deduplicationEnabled = env('UNIFIED_LOG_DEDUP', env('DEMO_LOG_DEDUP', 'true')) !== 'false'
  const aggregateLogs = env('UNIFIED_LOG_AGGREGATE', env('DEMO_LOG_AGGREGATE', 'true')) !== 'false'
  const testCodeLoggingEnabled = env('UNIFIED_LOG_TEST_CODE', env('DEMO_LOG_TEST_CODE', 'true')) !== 'false'

  // 根据日志级别确定静默模式
  let quietMode = true
  if (logLevel === 'verbose') {
    quietMode = false
  } else if (logLevel === 'silent') {
    quietMode = true
  } else if (logLevel === 'normal') {
    quietMode = false
  }
  // 'mini' 模式 - 静默且最小输出

  return {
    quietMode,
    deduplicationEnabled,
    logLevel,
    aggregateLogs,
    testCodeLoggingEnabled,
    compactMode: env('UNIFIED_LOG_COMPACT', env('DEMO_LOG_COMPACT', 'false')) === 'true'
  }
}

/**
 * 是否完全静默（不输出任何内容）
 */
export function isSilentMode(): boolean {
  const level = process.env.UNIFIED_LOG_LEVEL || process.env.DEMO_LOG_LEVEL
  return level === 'silent'
}

/**
 * 是否详细输出模式
 */
export function isVerboseMode(): boolean {
  const level = process.env.UNIFIED_LOG_LEVEL || process.env.DEMO_LOG_LEVEL
  return level === 'verbose'
}

/**
 * 是否迷你输出模式（默认）
 */
export function isMiniMode(): boolean {
  const level = process.env.UNIFIED_LOG_LEVEL || process.env.DEMO_LOG_LEVEL
  return !level || level === 'mini'
}

/**
 * 格式化日志文件路径的显示信息
 */
export function formatLogPath(logFile: string): {
  context: string
  absolute: string
  display: string
} {
  const absolutePath = path.resolve(logFile)
  const relativePath = path.relative(process.cwd(), logFile)
  const projectName = path.basename(path.dirname(process.cwd()))

  return {
    context: `[${projectName}] ${relativePath}`,
    absolute: absolutePath,
    display: `[${projectName}] ${relativePath}\n  Full: ${absolutePath}`
  }
}
```

---

## 5. packages/playwright-unified-logger/src/console-logger.ts

```typescript
/**
 * Console Logger - 浏览器控制台日志捕获器
 *
 * 用途：
 * - 捕获 Playwright Page 的浏览器控制台消息
 * - 智能过滤无害的开发环境噪音（React DevTools、HMR 警告等）
 * - 日志去重，减少重复输出
 * - 自动写入文件，供 AI 分析和调试使用
 *
 * 使用方式：
 * ```typescript
 * const logger = new ConsoleLogger(page, 'test-title')
 * // ... 测试逻辑 ...
 * await logger.finalize()
 * ```
 */

import { Page, ConsoleMessage } from '@playwright/test'
import * as fs from 'fs/promises'
import * as path from 'path'

export interface ConsoleLogEntry {
  timestamp: string
  type: string
  text: string
  location?: string
}

/**
 * 常见无害的控制台消息模式，可安全过滤
 */
const FILTERED_PATTERNS = [
  /Download the React DevTools/i,
  /Install the React DevTools/i,
  /Warning: ReactDOM\.render/i,
  /Warning: react-dom/i,
  /experimental/i,
  /HMR/i,
  /SourceMap/i,
  /sourcemapped/i,
  /Google Maps/i,
  /Recaptcha/i,
  /Stripe/i,
  /net::ERR_BLOCKED_BY_CLIENT/i,
  /net::ERR_FAILED/i,
]

export class ConsoleLogger {
  private logs: ConsoleLogEntry[] = []
  private page: Page
  public logFile: string
  private quietMode: boolean
  private compactMode: boolean
  private deduplicationEnabled: boolean
  private filteringEnabled: boolean
  private seenLogs = new Set<string>()
  private filteredCount = 0

  constructor(
    page: Page,
    testTitle: string,
    quietMode = false,
    deduplicationEnabled = true,
    filteringEnabled = true,
    compactMode = false
  ) {
    this.page = page
    this.quietMode = quietMode
    this.compactMode = compactMode
    this.deduplicationEnabled = deduplicationEnabled
    this.filteringEnabled = filteringEnabled

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const safeTestTitle = testTitle.replace(/[^a-zA-Z0-9\-_]/g, '_')
    const runId = process.env.UNIFIED_RUN_ID || process.env.DEMO_RUN_ID || 'no-run-id'

    this.logFile = path.resolve(
      process.cwd(), 'test-results', 'unified-logs',
      `${runId}-${safeTestTitle}-${timestamp}.log`
    )

    this.attachListeners()
  }

  private shouldFilter(entry: ConsoleLogEntry): boolean {
    if (!this.filteringEnabled || entry.type === 'error') {
      return false
    }
    return FILTERED_PATTERNS.some(pattern => pattern.test(entry.text))
  }

  private isDuplicate(entry: ConsoleLogEntry): boolean {
    if (!this.deduplicationEnabled) {
      return false
    }
    const logKey = `${entry.type}:${entry.text}`
    if (this.seenLogs.has(logKey)) {
      return true
    }
    this.seenLogs.add(logKey)
    return false
  }

  private addLog(entry: ConsoleLogEntry, skipDeduplication = false): boolean {
    if (skipDeduplication || !this.isDuplicate(entry)) {
      this.logs.push(entry)
      return true
    }
    return false
  }

  private attachListeners() {
    this.page.on('console', async (msg: ConsoleMessage) => {
      const entry: ConsoleLogEntry = {
        timestamp: new Date().toISOString(),
        type: msg.type(),
        text: msg.text(),
        location: msg.location()?.url,
      }

      if (this.shouldFilter(entry)) {
        this.filteredCount++
        await this.writeLog(entry, false, true)
        return
      }

      const isDuplicate = !this.addLog(entry)
      await this.writeLog(entry, isDuplicate, false)
    })

    // 区分未处理的 Promise 拒绝（warning）和其他页面错误（error）
    this.page.on('pageerror', async (error: Error) => {
      const isUnhandledRejection = error.message.includes('UnhandledPromiseRejection')
      const entry: ConsoleLogEntry = {
        timestamp: new Date().toISOString(),
        type: isUnhandledRejection ? 'warning' : 'error',
        text: isUnhandledRejection
          ? error.message
          : `${error.message}\n${error.stack}`,
      }
      const isDuplicate = !this.addLog(entry, !isUnhandledRejection)
      await this.writeLog(entry, isDuplicate, false)
    })
  }

  private async writeLog(entry: ConsoleLogEntry, isDuplicate: boolean = false, isFiltered: boolean = false) {
    const dedupMarker = isDuplicate ? ' [DUPLICATE]' : ''
    const filterMarker = isFiltered ? ' [FILTERED]' : ''
    const logLine = `[${entry.timestamp}] [${entry.type.toUpperCase()}]${dedupMarker}${filterMarker} ${entry.text}${entry.location ? ` (${entry.location})` : ''}\n`

    try {
      await fs.mkdir(path.dirname(this.logFile), { recursive: true })
      await fs.appendFile(this.logFile, logLine)
    } catch (error) {
      console.error('[ConsoleLogger] Failed to write log:', error)
    }
  }

  async finalize() {
    const dedupStats = this.getDeduplicationStats()
    const summary = {
      totalLogs: this.logs.length,
      uniqueLogs: this.logs.length,
      duplicatesFiltered: dedupStats.duplicatesFiltered,
      filteredCount: this.filteredCount,
      errors: this.logs.filter(l => l.type === 'error').length,
      warnings: this.logs.filter(l => l.type === 'warning').length,
      timestamp: new Date().toISOString(),
    }

    if (this.quietMode) {
      this.printQuietSummary(summary)
    } else {
      this.printVerboseSummary(summary)
    }
  }

  private printQuietSummary(summary: { errors: number; warnings: number }): void {
    const dedupStats = this.getDeduplicationStats()
    const opt = [
      dedupStats.duplicatesFiltered && `${dedupStats.duplicatesFiltered}d`,
      this.filteredCount && `${this.filteredCount}f`
    ].filter(Boolean).join(',')

    if (this.compactMode) {
      console.log(`[Con] ${summary.errors}e/${summary.warnings}w${opt ? ` (${opt})` : ''}`)
      return
    }

    const relativePath = path.relative(process.cwd(), this.logFile)
    console.log(`[Con] ${summary.errors}e/${summary.warnings}w${opt ? ` (${opt})` : ''} → ${relativePath}`)
  }

  private printVerboseSummary(summary: { errors: number; warnings: number }): void {
    const dedupStats = this.getDeduplicationStats()
    console.log(`[ConsoleLogger] Logs written to: ${this.logFile}`)
    console.log(`  Absolute path: ${path.resolve(this.logFile)}`)
    console.log(`[ConsoleLogger] Summary: ${summary.errors} errors, ${summary.warnings} warnings`)

    if (dedupStats.duplicatesFiltered > 0) {
      console.log(`[ConsoleLogger] Deduplication: ${dedupStats.duplicatesFiltered} duplicates filtered`)
    }
    if (this.filteredCount > 0) {
      console.log(`[ConsoleLogger] Filtering: ${this.filteredCount} messages filtered`)
    }
  }

  getDeduplicationStats(): { duplicatesFiltered: number; uniqueLogs: number } {
    if (!this.deduplicationEnabled) {
      return { duplicatesFiltered: 0, uniqueLogs: this.logs.length }
    }
    return {
      duplicatesFiltered: this.seenLogs.size - this.logs.length,
      uniqueLogs: this.logs.length
    }
  }

  getLogs(): ConsoleLogEntry[] {
    return this.logs
  }

  clearLogs() {
    this.logs = []
  }
}
```

---

## 6. packages/playwright-unified-logger/src/network-logger.ts

```typescript
/**
 * Network Logger - API 请求监听器
 *
 * 用途：
 * - 捕获所有 API 请求和响应（含请求头、Cookie、请求体）
 * - 自动脱敏敏感信息（密码、Token）
 * - 支持 Request ID 关联，便于前后端日志对应
 * - 请求聚合统计，减少输出噪音
 * - 响应体自动截断（上限 5000 字符）
 *
 * 使用方式：
 * ```typescript
 * const logger = new NetworkLogger(page)
 * // ... 测试逻辑 ...
 * logger.printLogs('API Summary')
 * ```
 */

import { Page } from '@playwright/test'

export interface ApiRequestLog {
  timestamp: string
  method: string
  url: string
  status?: number
  contentType?: string
  requestHeaders?: Record<string, string>
  requestCookie?: string
  requestBodyRaw?: string
  requestBody?: string
  bodyRedacted?: boolean
  responseBody?: string
  duration?: number
  error?: string
  requestId?: string
  responseSetCookie?: string
  pageCookies?: string
}

export class NetworkLogger {
  private logs: ApiRequestLog[] = []
  private page!: Page
  private requestStartTimes: Map<string, number> = new Map()
  private quietMode: boolean

  constructor(page: Page, quietMode: boolean = false) {
    this.page = page
    this.quietMode = quietMode
    this.attachListeners()
  }

  private attachListeners() {
    // 监听所有请求
    this.page.on('request', async (request) => {
      const url = request.url()
      if (this.isApiRequest(url)) {
        const headers = request.headers()
        const requestCookie = headers['cookie'] || headers['Cookie']
        const requestHeaders = this.pickReplayHeaders(headers)

        // 获取页面级别的所有 cookies
        let pageCookies = ''
        try {
          const cookies = await this.page.context().cookies()
          pageCookies = cookies.map(c => `${c.name}=${c.value}`).join('; ')
        } catch {
          // 忽略错误
        }

        const log: ApiRequestLog = {
          timestamp: new Date().toISOString(),
          method: request.method(),
          url: url,
          contentType: headers['content-type'],
          requestId: headers['x-request-id'],
          requestHeaders,
          requestCookie,
          pageCookies,
        }

        this.requestStartTimes.set(url, Date.now())

        // 记录请求体（脱敏处理）
        try {
          const postData = request.postData()
          if (postData) {
            log.requestBodyRaw = postData
            log.requestBody = this.sanitizeData(postData)
            log.bodyRedacted = log.requestBody !== postData
          }
        } catch {
          // 忽略解析错误
        }

        this.logs.push(log)
      }
    })

    // 监听所有响应
    this.page.on('response', async (response) => {
      const url = response.url()
      if (this.isApiRequest(url)) {
        const log = this.logs.find((l) => l.url === url && !l.status)

        if (log) {
          const responseHeaders = response.headers()
          log.status = response.status()
          log.contentType = responseHeaders['content-type']

          if (responseHeaders['set-cookie']) {
            log.responseSetCookie = this.sanitizeCookie(responseHeaders['set-cookie'])
          }

          if (responseHeaders['x-request-id']) {
            log.requestId = responseHeaders['x-request-id']
          }

          const startTime = this.requestStartTimes.get(url)
          if (startTime) {
            log.duration = Date.now() - startTime
            this.requestStartTimes.delete(url)
          }

          try {
            const body = await response.text()
            if (body && body.length < 5000) {
              log.responseBody = body
            } else if (body) {
              log.responseBody = body.substring(0, 5000) + '... (truncated)'
            }
          } catch {
            // 忽略解析错误
          }
        }
      }
    })

    // 监听请求失败
    this.page.on('requestfailed', (request) => {
      const url = request.url()
      if (this.isApiRequest(url)) {
        const log = this.logs.find((l) => l.url === url && !l.error)

        if (log) {
          log.error = request.failure()?.errorText || 'Unknown error'

          const startTime = this.requestStartTimes.get(url)
          if (startTime) {
            log.duration = Date.now() - startTime
            this.requestStartTimes.delete(url)
          }
        }
      }
    })
  }

  /**
   * 判断是否为 API 请求
   * 匹配 /api/ 或 /_api/ 路径
   */
  private isApiRequest(url: string): boolean {
    return url.includes('/api/') || url.includes('/_api/')
  }

  /**
   * 脱敏处理：隐藏密码、密钥、Token 等敏感信息
   */
  private sanitizeData(data: string): string {
    try {
      const parsed = JSON.parse(data)
      const sanitized = JSON.parse(JSON.stringify(parsed), (key, value) => {
        if (typeof value === 'string' && (
          key.toLowerCase().includes('password') ||
          key.toLowerCase().includes('secret') ||
          key.toLowerCase().includes('token') ||
          key.toLowerCase().includes('currentpassword') ||
          key.toLowerCase().includes('newpassword')
        )) {
          return '***REDACTED***'
        }
        return value
      })
      return JSON.stringify(sanitized)
    } catch {
      return data.replace(/"password":"[^"]*"/g, '"password":"***REDACTED***"')
    }
  }

  /**
   * Cookie 脱敏：认证相关 Cookie 值替换为 ***REDACTED***
   */
  private sanitizeCookie(setCookie: string): string {
    const cookies = setCookie.split('\n')
    return cookies.map(cookie => {
      const match = cookie.match(/^([^=]+)=([^;]+)/)
      if (match) {
        const name = match[1]
        const authCookieNames = ['x-auth', 'x-auth-refresh', 'token', 'session', 'sid', 'jwt']
        if (authCookieNames.includes(name.toLowerCase())) {
          return cookie.replace(match[2], '***REDACTED***')
        }
      }
      return cookie
    }).join('\n')
  }

  /**
   * 提取用于 API 重放的请求头
   */
  private pickReplayHeaders(headers: Record<string, string>): Record<string, string> {
    const keep = ['content-type', 'accept', 'authorization', 'x-request-id', 'cookie', 'user-agent']
    const selected: Record<string, string> = {}
    for (const [key, value] of Object.entries(headers)) {
      if (keep.includes(key.toLowerCase())) {
        selected[key] = value
      }
    }
    return selected
  }

  printLogs(title?: string) {
    if (this.logs.length === 0) {
      console.log('[Network] No API requests captured')
      return
    }

    console.log('\n' + '='.repeat(80))
    console.log(title || 'API Request Logs')
    console.log('='.repeat(80))

    for (const log of this.logs) {
      console.log(`\n[${log.timestamp}] ${log.method} ${log.url}`)
      if (log.requestId) console.log(`  Request ID: ${log.requestId}`)
      if (log.requestCookie) console.log(`  Cookie: ${log.requestCookie}`)
      if (log.pageCookies) console.log(`  Page Cookies: ${log.pageCookies}`)
      if (log.requestBody) console.log(`  → Request: ${log.requestBody}`)

      if (log.status) {
        const statusIcon = log.status >= 200 && log.status < 300 ? '✓' : '✗'
        console.log(`  ← Response: ${statusIcon} ${log.status}${log.duration ? ` (${log.duration}ms)` : ''}`)
        if (log.responseSetCookie) console.log(`  Set-Cookie: ${log.responseSetCookie}`)
        if (log.responseBody) {
          try {
            const parsed = JSON.parse(log.responseBody)
            const formatted = JSON.stringify(parsed, null, 2)
            console.log(`    Body:\n${formatted.split('\n').join('\n    ')}`)
          } catch {
            console.log(`    Body: ${log.responseBody}`)
          }
        }
      }

      if (log.error) {
        console.log(`  ✗ Error: ${log.error}${log.duration ? ` (${log.duration}ms)` : ''}`)
      }
    }

    console.log('\n' + '='.repeat(80))
  }

  printFailedLogs(title?: string) {
    const failedLogs = this.logs.filter(log =>
      log.error || (log.status && log.status >= 400)
    )

    if (failedLogs.length === 0) {
      console.log('[Network] All API requests successful')
      return
    }

    console.log('\n' + '='.repeat(80))
    console.log(title || 'Failed API Requests')
    console.log('='.repeat(80))

    for (const log of failedLogs) {
      console.log(`\n[${log.timestamp}] ${log.method} ${log.url}`)
      if (log.requestCookie) console.log(`  Cookie: ${log.requestCookie}`)
      if (log.pageCookies) console.log(`  Page Cookies: ${log.pageCookies}`)
      if (log.requestBody) console.log(`  → Request: ${log.requestBody}`)

      if (log.status) {
        console.log(`  ← Response: ✗ ${log.status}${log.duration ? ` (${log.duration}ms)` : ''}`)
        if (log.responseSetCookie) console.log(`  Set-Cookie: ${log.responseSetCookie}`)
        if (log.responseBody) {
          try {
            const parsed = JSON.parse(log.responseBody)
            const formatted = JSON.stringify(parsed, null, 2)
            console.log(`    Body:\n${formatted.split('\n').join('\n    ')}`)
          } catch {
            console.log(`    Body: ${log.responseBody}`)
          }
        }
      }

      if (log.error) {
        console.log(`  ✗ Error: ${log.error}${log.duration ? ` (${log.duration}ms)` : ''}`)
      }
    }

    console.log('\n' + '='.repeat(80))
  }

  getLogs(): ApiRequestLog[] {
    return this.logs
  }

  clearLogs() {
    this.logs = []
    this.requestStartTimes.clear()
  }

  exportToJson(): string {
    return JSON.stringify(this.logs, null, 2)
  }

  getFailedLogs(): ApiRequestLog[] {
    return this.logs.filter(log =>
      log.error || (log.status && log.status >= 400)
    )
  }

  findLogsByRequestId(requestId: string): ApiRequestLog[] {
    return this.logs.filter(log => log.requestId === requestId)
  }

  getLogsWithRequestId(): ApiRequestLog[] {
    return this.logs.filter(log => log.requestId)
  }

  /**
   * Mini 摘要 - 单行输出，减少 Token 消耗
   */
  printMiniSummary(title?: string) {
    const failed = this.getFailedLogs()
    const aggregated = this.getAggregatedLogs()
    const uniqueRequests = Object.keys(aggregated).length

    console.log(`[Network] ${title || 'Summary'}: ${this.logs.length} requests (${uniqueRequests} unique), ${failed.length} failed`)

    if (failed.length > 0 && failed.length <= 5) {
      failed.forEach(f => {
        const status = f.status || (f.error ? 'ERR' : '?')
        console.log(`  ${f.method} ${f.url} → ${status}`)
      })
    } else if (failed.length > 5) {
      console.log(`  (First 5 of ${failed.length} failed requests)`)
      failed.slice(0, 5).forEach(f => {
        const status = f.status || (f.error ? 'ERR' : '?')
        console.log(`  ${f.method} ${f.url} → ${status}`)
      })
    }
  }

  /**
   * 聚合相似请求，按 method + path 分组
   */
  getAggregatedLogs(): Record<string, { count: number; successCount: number; failureCount: number; avgDuration?: number }> {
    const aggregated: Record<string, { count: number; successCount: number; failureCount: number; totalDuration: number }> = {}

    for (const log of this.logs) {
      const url = new URL(log.url, 'http://localhost')
      const path = url.pathname
      const key = `${log.method} ${path}`

      if (!aggregated[key]) {
        aggregated[key] = { count: 0, successCount: 0, failureCount: 0, totalDuration: 0 }
      }

      aggregated[key].count++
      if (log.status && log.status >= 200 && log.status < 300) {
        aggregated[key].successCount++
      } else if (log.status && log.status >= 400 || log.error) {
        aggregated[key].failureCount++
      }
      if (log.duration) {
        aggregated[key].totalDuration += log.duration
      }
    }

    const result: Record<string, { count: number; successCount: number; failureCount: number; avgDuration?: number }> = {}
    for (const [key, value] of Object.entries(aggregated)) {
      result[key] = {
        count: value.count,
        successCount: value.successCount,
        failureCount: value.failureCount,
        avgDuration: value.totalDuration > 0 ? Math.round(value.totalDuration / value.count) : undefined
      }
    }

    return result
  }

  /**
   * 打印聚合请求摘要
   */
  printAggregatedLogs(title?: string) {
    const aggregated = this.getAggregatedLogs()
    const entries = Object.entries(aggregated).sort((a, b) => b[1].count - a[1].count)

    console.log('\n' + '='.repeat(80))
    console.log(title || 'Aggregated API Requests')
    console.log('='.repeat(80))

    for (const [key, stats] of entries) {
      const statusIcon = stats.failureCount === 0 ? '✓' : '✗'
      const durationStr = stats.avgDuration ? ` (${stats.avgDuration}ms avg)` : ''
      console.log(`  ${statusIcon} ${key}: ${stats.count}x [${stats.successCount} success, ${stats.failureCount} failed]${durationStr}`)
    }

    console.log('='.repeat(80))
  }
}
```

---

## 7. packages/playwright-unified-logger/src/route-logger.ts

```typescript
/**
 * Route Logger - 页面路由变化监听器
 *
 * 用途：
 * - 捕获 SPA 路由变化（导航历史）
 * - 检测自动重定向（如 Session 持久化导致的重定向）
 * - 追踪用户操作路径
 * - 辅助诊断导航问题
 */

import { Page } from '@playwright/test'

export interface RouteChangeLog {
  timestamp: string
  url: string
  title?: string
  trigger?: 'goto' | 'redirect' | 'back_forward' | 'unknown'
}

export class RouteLogger {
  private routeLogs: RouteChangeLog[] = []
  private page!: Page
  private quietMode: boolean
  private lastUrl: string = ''

  constructor(page: Page, quietMode: boolean = false) {
    this.page = page
    this.quietMode = quietMode
    this.attachListeners()
  }

  private attachListeners() {
    this.page.on('framenavigated', async (frame) => {
      if (frame === this.page.mainFrame()) {
        const url = frame.url()
        const title = await frame.title().catch(() => '')

        if (url !== this.lastUrl) {
          const log: RouteChangeLog = {
            timestamp: new Date().toISOString(),
            url: url,
            title: title || undefined,
            trigger: this.detectTriggerType(url)
          }

          this.routeLogs.push(log)
          this.lastUrl = url

          if (this.quietMode) {
            const triggerIcon = this.getTriggerIcon(log.trigger)
            console.log(`[Route] ${triggerIcon} ${url}`)
          }
        }
      }
    })
  }

  private detectTriggerType(url: string): 'goto' | 'redirect' | 'back_forward' | 'unknown' {
    if (url.includes('/redirect') || url.includes('?redirect')) {
      return 'redirect'
    }
    return 'unknown'
  }

  private getTriggerIcon(trigger?: string): string {
    switch (trigger) {
      case 'goto': return '→'
      case 'redirect': return '↝'
      case 'back_forward': return '↔'
      default: return '→'
    }
  }

  printRouteChanges(title?: string) {
    if (this.routeLogs.length === 0) {
      console.log('[Route] No route changes captured')
      return
    }

    console.log('\n' + '='.repeat(80))
    console.log(title || 'Route Changes')
    console.log('='.repeat(80))

    for (let i = 0; i < this.routeLogs.length; i++) {
      const log = this.routeLogs[i]
      const triggerIcon = this.getTriggerIcon(log.trigger)
      const stepNum = i + 1

      console.log(`\n[${stepNum}] ${log.timestamp}`)
      if (log.title) {
        console.log(`  ${triggerIcon} ${log.url}`)
        console.log(`     Title: "${log.title}"`)
      } else {
        console.log(`  ${triggerIcon} ${log.url}`)
      }
      if (log.trigger) {
        console.log(`     Trigger: ${log.trigger}`)
      }

      if (i > 0 && this.isPossibleRedirect(this.routeLogs[i - 1].url, log.url)) {
        console.log(`     ⚠️  Possible auto-redirect detected`)
      }
    }

    console.log('\n' + '='.repeat(80))
  }

  private isPossibleRedirect(fromUrl: string, toUrl: string): boolean {
    const isFromAuth = fromUrl.includes('/login') || fromUrl.includes('/register')
    const isToDashboard = toUrl.includes('/dashboard') || toUrl.includes('/manage')
    return isFromAuth && isToDashboard
  }

  printMiniSummary(title?: string) {
    const redirectCount = this.detectRedirectCount()
    console.log(`[Route] ${title || 'Summary'}: ${this.routeLogs.length} changes${redirectCount > 0 ? ` (${redirectCount} possible redirects)` : ''}`)

    if (this.routeLogs.length > 0) {
      const recent = this.routeLogs.slice(-3)
      recent.forEach((log, idx) => {
        const triggerIcon = this.getTriggerIcon(log.trigger)
        const prefix = this.routeLogs.length > 3
          ? `... +${this.routeLogs.length - 3} more, then `
          : `${this.routeLogs.length - recent.length + idx + 1}. `
        console.log(`  ${prefix}${triggerIcon} ${this.shortenUrl(log.url)}`)
      })
    }
  }

  private shortenUrl(url: string): string {
    try {
      const urlObj = new URL(url)
      const path = urlObj.pathname
      const segments = path.split('/').filter(s => s)
      if (segments.length > 2) {
        return '.../' + segments.slice(-2).join('/')
      }
      return path || url
    } catch {
      return url.length > 50 ? url.substring(0, 50) + '...' : url
    }
  }

  private detectRedirectCount(): number {
    let count = 0
    for (let i = 1; i < this.routeLogs.length; i++) {
      if (this.isPossibleRedirect(this.routeLogs[i - 1].url, this.routeLogs[i].url)) {
        count++
      }
    }
    return count
  }

  getRouteLogs(): RouteChangeLog[] {
    return this.routeLogs
  }

  clearRouteLogs() {
    this.routeLogs = []
    this.lastUrl = ''
  }

  exportToJson(): string {
    return JSON.stringify(this.routeLogs, null, 2)
  }

  analyzeRoutePattern(): {
    totalChanges: number
    possibleRedirects: number
    authPages: number
    dashboardPages: number
    lastUrl: string
  } {
    const authPages = this.routeLogs.filter(log =>
      log.url.includes('/login') || log.url.includes('/register')
    ).length

    const dashboardPages = this.routeLogs.filter(log =>
      log.url.includes('/dashboard')
    ).length

    return {
      totalChanges: this.routeLogs.length,
      possibleRedirects: this.detectRedirectCount(),
      authPages,
      dashboardPages,
      lastUrl: this.routeLogs.length > 0 ? this.routeLogs[this.routeLogs.length - 1].url : ''
    }
  }
}
```

---

## 8. packages/playwright-unified-logger/src/test-code-logger.ts

```typescript
/**
 * Test Code Logger - Node.js 测试代码日志捕获器
 *
 * 用途：
 * - 拦截 Node.js console.log/warn/error/info 输出
 * - 捕获测试代码中的 console 调用（区别于浏览器控制台）
 * - 记录源码位置（test-file.ts:line）
 * - 保留原始 console 功能，不影响测试输出
 *
 * 日志格式：[timestamp] [TYPE] [TEST_CODE] message (test-file.ts:line)
 */

import * as fs from 'fs'
import * as path from 'path'

export interface TestCodeLogEntry {
  timestamp: string
  type: 'log' | 'info' | 'warn' | 'error'
  message: string
  sourceLocation?: string
}

type ConsoleMethod = 'log' | 'info' | 'warn' | 'error'

export class TestCodeLogger {
  private logs: TestCodeLogEntry[] = []
  private logFile: string
  private enabled: boolean
  private initialized = false
  private originalConsole: Map<ConsoleMethod, typeof console.log> = new Map()

  constructor(logFile: string, enabled: boolean = true) {
    this.logFile = logFile
    this.enabled = enabled

    if (this.enabled) {
      this.initialize()
    }
  }

  private initialize(): void {
    if (this.initialized || !this.enabled) {
      return
    }

    const methods: ConsoleMethod[] = ['log', 'info', 'warn', 'error']

    for (const method of methods) {
      this.originalConsole.set(method, console[method])
      console[method] = ((...args: unknown[]) => {
        this.captureLog(method, args)
        this.originalConsole.get(method)!.apply(console, args)
      }) as typeof console.log
    }

    this.initialized = true
  }

  private captureLog(type: 'log' | 'info' | 'warn' | 'error', args: unknown[]): void {
    if (!this.enabled) {
      return
    }

    const entry: TestCodeLogEntry = {
      timestamp: new Date().toISOString(),
      type,
      message: this.formatMessage(args),
      sourceLocation: this.extractSourceLocation(),
    }

    this.logs.push(entry)
    this.writeToFile(entry)
  }

  private formatMessage(args: unknown[]): string {
    return args.map(formatArgument).join(' ')
  }

  /**
   * 从堆栈跟踪提取源码位置
   * 返回格式："test-file.ts:line"
   */
  private extractSourceLocation(): string | undefined {
    const stack = new Error().stack
    if (!stack) {
      return undefined
    }

    const lines = stack.split('\n')
    const patterns = [
      /\(([^:]+\.e2e\.ts):(\d+):\d+\)/,
      /\(([^:]+\.spec\.ts):(\d+):\d+\)/,
      /at\s+([^:]+\.e2e\.ts):(\d+)/,
      /at\s+([^:]+\.spec\.ts):(\d+)/,
    ]

    for (let i = 4; i < lines.length; i++) {
      for (const pattern of patterns) {
        const match = lines[i].match(pattern)
        if (match) {
          return `${path.basename(match[1])}:${match[2]}`
        }
      }
    }

    return undefined
  }

  private writeToFile(entry: TestCodeLogEntry): void {
    try {
      const logLine = this.formatLogLine(entry)
      const logDir = path.dirname(this.logFile)
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true })
      }
      fs.appendFileSync(this.logFile, logLine + '\n')
    } catch {
      // 静默失败，避免无限递归
    }
  }

  private formatLogLine(entry: TestCodeLogEntry): string {
    const timestamp = entry.timestamp
    const type = entry.type.toUpperCase()
    const location = entry.sourceLocation ? ` (${entry.sourceLocation})` : ''
    return `[${timestamp}] [${type}] [TEST_CODE] ${entry.message}${location}`
  }

  /**
   * 恢复原始 console 方法（测试结束时调用）
   */
  restoreConsole(): void {
    if (!this.initialized) {
      return
    }

    for (const [method, originalFn] of this.originalConsole.entries()) {
      console[method] = originalFn
    }

    this.initialized = false
  }

  getLogs(): TestCodeLogEntry[] {
    return this.logs
  }

  getLogsByType(type: 'log' | 'info' | 'warn' | 'error'): TestCodeLogEntry[] {
    return this.logs.filter(log => log.type === type)
  }

  getErrorLogs(): TestCodeLogEntry[] {
    return this.getLogsByType('error')
  }

  getWarningLogs(): TestCodeLogEntry[] {
    return this.getLogsByType('warn')
  }

  clearLogs(): void {
    this.logs = []
  }

  log(...args: unknown[]): void {
    this.captureLog('log', args)
    this.originalConsole.get('log')!.apply(console, args)
  }

  info(...args: unknown[]): void {
    this.captureLog('info', args)
    this.originalConsole.get('info')!.apply(console, args)
  }

  warn(...args: unknown[]): void {
    this.captureLog('warn', args)
    this.originalConsole.get('warn')!.apply(console, args)
  }

  error(...args: unknown[]): void {
    this.captureLog('error', args)
    this.originalConsole.get('error')!.apply(console, args)
  }
}

/**
 * 格式化单个参数为字符串
 */
function formatArgument(arg: unknown): string {
  if (typeof arg === 'string') {
    return arg
  }
  if (arg instanceof Error) {
    return `${arg.name}: ${arg.message}`
  }
  if (arg === null) {
    return 'null'
  }
  if (arg === undefined) {
    return 'undefined'
  }
  if (typeof arg === 'object') {
    try {
      return JSON.stringify(arg, null, 2)
    } catch {
      return String(arg)
    }
  }
  return String(arg)
}
```

---

## 9. packages/playwright-unified-logger/src/unified-logger.ts

```typescript
/**
 * Unified Logger - 统一日志协调器
 *
 * 整合 NetworkLogger、ConsoleLogger、RouteLogger 和 TestCodeLogger，
 * 提供统一的日志记录接口。
 *
 * 所有日志自动写入文件，便于 AI 分析和调试。
 *
 * 使用方式：
 * ```typescript
 * import { UnifiedLogger } from '{{PROJECT_NAME}}-playwright-unified-logger'
 *
 * // 在 Playwright fixture 中创建
 * const logger = new UnifiedLogger(page, testInfo.title)
 *
 * // ... 测试逻辑 ...
 *
 * // 测试结束时打印摘要并保存日志文件
 * logger.printSummary('Test Summary')
 * const logs = await logger.finalize()
 * ```
 */

import { Page } from '@playwright/test'
import * as path from 'path'
import * as fs from 'fs'
import { NetworkLogger } from './network-logger'
import { ConsoleLogger } from './console-logger'
import { RouteLogger } from './route-logger'
import { TestCodeLogger } from './test-code-logger'
import { getLoggerConfig, LoggerConfig } from './log-config'

export interface TestLogs {
  networkLogs: string
  consoleLogs: string
  timestamp: string
}

export class UnifiedLogger {
  public network: NetworkLogger
  public console: ConsoleLogger
  public route: RouteLogger
  public testCode: TestCodeLogger
  private quietMode: boolean
  private compactMode: boolean
  private config: LoggerConfig

  constructor(page: Page, testTitle: string, quietMode?: boolean) {
    this.config = getLoggerConfig()
    this.quietMode = quietMode ?? this.config.quietMode
    this.compactMode = this.config.compactMode

    this.network = new NetworkLogger(page, this.quietMode)
    this.console = new ConsoleLogger(page, testTitle, this.quietMode, this.config.deduplicationEnabled, true, this.compactMode)
    this.route = new RouteLogger(page, this.quietMode)
    this.testCode = new TestCodeLogger(this.console.logFile, this.config.testCodeLoggingEnabled)
  }

  /**
   * 完成日志记录，保存网络日志文件，返回所有日志路径
   * 必须在测试结束时调用（通常在 fixture 的 afterUse 中）
   */
  async finalize(): Promise<TestLogs> {
    // 恢复原始 console 方法（必须在 console.finalize() 之前）
    this.testCode.restoreConsole()
    await this.console.finalize()

    const baseName = this.console.logFile.replace(/\.log$/, '')

    // 保存完整的网络日志到 JSON 文件
    const networkLogFile = `${baseName}-network.json`
    const networkLogsData = this.network.exportToJson()
    fs.writeFileSync(networkLogFile, networkLogsData)

    return {
      networkLogs: networkLogFile,
      consoleLogs: this.console.logFile,
      timestamp: new Date().toISOString()
    }
  }

  /**
   * 打印日志摘要
   * - quietMode → 单行迷你摘要
   * - verbose → 完整详细摘要
   */
  printSummary(title: string) {
    if (this.quietMode) {
      this.printMiniSummary(title)
      return
    }
    this.printVerboseSummary(title)
  }

  private printVerboseSummary(title: string): void {
    console.log(`\n=== ${title} ===`)
    this.network.printLogs(title)
    this.route.printRouteChanges(title)
    console.log(`\nConsole logs: ${this.console.logFile}`)
    console.log(`\n[Summary]`)

    const logs = this.network.getLogs()
    const failedLogs = this.network.getFailedLogs()
    const routeAnalysis = this.route.analyzeRoutePattern()
    const consoleLogs = this.console.getLogs()
    const testCodeLogs = this.testCode.getLogs()

    console.log(`  Network requests: ${logs.length}`)
    console.log(`  Failed requests: ${failedLogs.length}`)
    console.log(`  Route changes: ${routeAnalysis.totalChanges}`)
    console.log(`  Possible redirects: ${routeAnalysis.possibleRedirects}`)
    console.log(`  Console logs: ${consoleLogs.length}`)
    console.log(`  Console errors: ${consoleLogs.filter(l => l.type === 'error').length}`)
    console.log(`  Console warnings: ${consoleLogs.filter(l => l.type === 'warning').length}`)
    console.log(`  Test code logs: ${testCodeLogs.length}`)
    console.log(`  Test code errors: ${this.testCode.getErrorLogs().length}`)
    console.log(`  Test code warnings: ${this.testCode.getWarningLogs().length}`)
  }

  /**
   * Mini 摘要 - 单行输出，减少 Token 消耗
   */
  printMiniSummary(title?: string) {
    const logs = this.network.getLogs()
    const failedLogs = this.network.getFailedLogs()
    const consoleLogs = this.console.getLogs()
    const routeAnalysis = this.route.analyzeRoutePattern()
    const testCodeLogs = this.testCode.getLogs()
    const errors = consoleLogs.filter(l => l.type === 'error').length
    const warnings = consoleLogs.filter(l => l.type === 'warning').length

    if (this.compactMode) {
      console.log(`[${title || 'Uni'}] ${logs.length}r/${failedLogs.length}f ${errors}e/${warnings}w ${routeAnalysis.totalChanges}rt/${testCodeLogs.length}tl`)
      return
    }

    const relativePath = path.relative(process.cwd(), this.console.logFile)
    console.log(`[Uni] ${logs.length}r/${failedLogs.length}f ${errors}e/${warnings}w ${routeAnalysis.totalChanges}rt/${testCodeLogs.length}tl → ${relativePath}`)
  }

  /**
   * 仅打印失败的请求
   */
  printFailedLogs(title: string) {
    this.network.printFailedLogs(title)
  }

  /**
   * 打印路由变化
   */
  printRouteChanges(title?: string) {
    this.route.printRouteChanges(title)
  }
}
```
