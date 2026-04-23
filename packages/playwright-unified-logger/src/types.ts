/**
 * Shared types and interfaces for Playwright Unified Logger
 */

// ── Log Level ──

export type LogLevel = 'mini' | 'normal' | 'verbose' | 'silent'

// ── Log Entry Types ──

export interface ConsoleLogEntry {
  timestamp: string
  type: string
  text: string
  location?: string
}

export interface ApiRequestLog {
  /** Internal tracking ID */
  _internalId: string
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

export interface RouteChangeLog {
  timestamp: string
  url: string
  title?: string
  trigger?: 'goto' | 'redirect' | 'back_forward' | 'unknown'
}

export interface TestCodeLogEntry {
  timestamp: string
  type: 'log' | 'info' | 'warn' | 'error'
  message: string
  sourceLocation?: string
}

// ── Configuration ──

export interface NetworkLoggerOptions {
  /** Filter function to identify API requests. Default: url includes /api/ or /_api/ */
  urlFilter?: (url: string) => boolean
  /** Max response body length to capture. Default: 5000 */
  maxResponseBodyLength?: number
  /** JSON keys to redact in request/response bodies. Default: ['password','secret','token','currentpassword','newpassword'] */
  sanitizeKeys?: string[]
  /** Headers to capture for replay. Default: ['content-type','accept','authorization','x-request-id','cookie','user-agent'] */
  replayHeaders?: string[]
  /** Cookie names whose values should be redacted. Default: ['x-auth','x-auth-refresh','token','session','sid','jwt'] */
  authCookieNames?: string[]
  /** Whether to capture page-level cookies per request. Default: true */
  captureCookies?: boolean
}

export interface ConsoleLoggerOptions {
  /** RegExp patterns for harmless console messages to filter out. Default: React DevTools, HMR, etc. */
  filterPatterns?: RegExp[]
  /** Whether filtering is enabled. Default: true */
  filteringEnabled?: boolean
}

export interface RouteLoggerOptions {
  /** Custom redirect detection function. Default: detects login→dashboard patterns */
  redirectDetector?: (fromUrl: string, toUrl: string) => boolean
  /** Custom route analysis function */
  routeAnalyzer?: (logs: RouteChangeLog[]) => RouteAnalysis
}

export interface TestCodeLoggerOptions {
  /** Whether to capture test code console output. Default: true */
  enabled?: boolean
  /** RegExp patterns for source file location extraction. Default: .e2e.ts and .spec.ts */
  sourceFilePatterns?: RegExp[]
}

export interface UnifiedLoggerConfig {
  /** Log output level. Default: 'mini' */
  logLevel?: LogLevel
  /** Compact single-line output mode. Default: false */
  compactMode?: boolean
  /** Output directory for log files. Default: 'test-results/unified-logs' */
  outputDir?: string
  /** Enable log deduplication. Default: true */
  deduplication?: boolean
  /** Enable request aggregation. Default: true */
  aggregation?: boolean

  network?: NetworkLoggerOptions
  console?: ConsoleLoggerOptions
  route?: RouteLoggerOptions
  testCode?: TestCodeLoggerOptions
}

// ── Output Types ──

export interface TestLogs {
  networkLogs: string
  consoleLogs: string
  routeLogs: string
  testCodeLogs: string
  timestamp: string
  summary: TestSummary
}

export interface TestSummary {
  networkRequests: number
  failedRequests: number
  routeChanges: number
  possibleRedirects: number
  consoleLogs: number
  consoleErrors: number
  consoleWarnings: number
  testCodeLogs: number
  testCodeErrors: number
  testCodeWarnings: number
}

export interface RouteAnalysis {
  totalChanges: number
  possibleRedirects: number
  authPages: number
  dashboardPages: number
  lastUrl: string
}

export interface AggregatedRequestStats {
  count: number
  successCount: number
  failureCount: number
  avgDuration?: number
}

// ── Deduplication Stats ──

export interface DeduplicationStats {
  duplicatesFiltered: number
  uniqueLogs: number
}

// ── Logger Events ──

export type LoggerEventType =
  | 'network:request'
  | 'network:response'
  | 'network:error'
  | 'console:message'
  | 'console:error'
  | 'route:change'
  | 'testcode:log'

export interface LoggerEvent {
  type: LoggerEventType
  data: ApiRequestLog | ConsoleLogEntry | RouteChangeLog | TestCodeLogEntry
}

export type LoggerEventHandler<T extends LoggerEvent['type']> = (
  event: Extract<LoggerEvent, { type: T }>
) => void
