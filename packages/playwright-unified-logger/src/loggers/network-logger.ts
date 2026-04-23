/**
 * Network Logger - API request/response capture
 *
 * Captures all API requests and responses with:
 * - Request ID correlation via WeakMap<Request, ...> (no URL collision)
 * - Configurable URL filtering, sanitization, and header capture
 * - Response body auto-truncation
 */

import { Page, Request, Response } from '@playwright/test'
import type { ApiRequestLog, NetworkLoggerOptions, AggregatedRequestStats } from '../types'
import { LoggerEventBus } from '../core/event-bus'
import { formatVerboseNetworkLogs, formatFailedNetworkLogs, formatMiniNetworkSummary, formatAggregatedNetworkLogs } from '../output/formatters'

/** Default URL filter: matches /api/ or /_api/ paths */
function defaultUrlFilter(url: string): boolean {
  return url.includes('/api/') || url.includes('/_api/')
}

const DEFAULT_SANITIZE_KEYS = ['password', 'secret', 'token', 'currentpassword', 'newpassword']
const DEFAULT_REPLAY_HEADERS = ['content-type', 'accept', 'authorization', 'x-request-id', 'cookie', 'user-agent']
const DEFAULT_AUTH_COOKIE_NAMES = ['x-auth', 'x-auth-refresh', 'token', 'session', 'sid', 'jwt']

export class NetworkLogger {
  private logs: ApiRequestLog[] = []
  private page: Page
  /** Map Playwright Request objects to their log entries (O(1), no URL collision) */
  private requestMap = new WeakMap<Request, ApiRequestLog>()
  private requestStartTimes = new WeakMap<Request, number>()
  private requestIdCounter = 0
  private quietMode: boolean
  private events: LoggerEventBus
  private options: Required<Pick<NetworkLoggerOptions, 'urlFilter' | 'maxResponseBodyLength' | 'sanitizeKeys' | 'replayHeaders' | 'authCookieNames' | 'captureCookies'>>

  constructor(
    page: Page,
    quietMode: boolean = false,
    events: LoggerEventBus,
    options?: NetworkLoggerOptions
  ) {
    this.page = page
    this.quietMode = quietMode
    this.events = events

    this.options = {
      urlFilter: options?.urlFilter ?? defaultUrlFilter,
      maxResponseBodyLength: options?.maxResponseBodyLength ?? 5000,
      sanitizeKeys: options?.sanitizeKeys ?? DEFAULT_SANITIZE_KEYS,
      replayHeaders: options?.replayHeaders ?? DEFAULT_REPLAY_HEADERS,
      authCookieNames: options?.authCookieNames ?? DEFAULT_AUTH_COOKIE_NAMES,
      captureCookies: options?.captureCookies ?? true,
    }

    this.attachListeners()
  }

  private attachListeners(): void {
    this.page.on('request', async (request) => {
      const url = request.url()
      if (!this.options.urlFilter(url)) return

      const headers = request.headers()
      const requestCookie = headers['cookie'] || headers['Cookie']
      const requestHeaders = this.pickReplayHeaders(headers)

      let pageCookies = ''
      if (this.options.captureCookies) {
        try {
          const cookies = await this.page.context().cookies()
          pageCookies = cookies.map(c => `${c.name}=${c.value}`).join('; ')
        } catch {
          // Ignore errors
        }
      }

      const internalId = `req_${++this.requestIdCounter}`
      const log: ApiRequestLog = {
        _internalId: internalId,
        timestamp: new Date().toISOString(),
        method: request.method(),
        url: url,
        contentType: headers['content-type'],
        requestId: headers['x-request-id'],
        requestHeaders,
        requestCookie,
        pageCookies,
      }

      this.requestStartTimes.set(request, Date.now())

      // Record request body (with sanitization)
      try {
        const postData = request.postData()
        if (postData) {
          log.requestBodyRaw = postData
          log.requestBody = this.sanitizeData(postData)
          log.bodyRedacted = log.requestBody !== postData
        }
      } catch {
        // Ignore parse errors
      }

      this.requestMap.set(request, log)
      this.logs.push(log)
      this.events.emit({ type: 'network:request', data: log })
    })

    this.page.on('response', async (response: Response) => {
      const request = response.request()
      const log = this.requestMap.get(request)
      if (!log) return

      const responseHeaders = response.headers()
      log.status = response.status()
      log.contentType = responseHeaders['content-type']

      if (responseHeaders['set-cookie']) {
        log.responseSetCookie = this.sanitizeCookie(responseHeaders['set-cookie'])
      }

      if (responseHeaders['x-request-id']) {
        log.requestId = responseHeaders['x-request-id']
      }

      const startTime = this.requestStartTimes.get(request)
      if (startTime) {
        log.duration = Date.now() - startTime
        this.requestStartTimes.delete(request)
      }

      try {
        const body = await response.text()
        if (body) {
          const maxLen = this.options.maxResponseBodyLength
          if (body.length < maxLen) {
            log.responseBody = body
          } else {
            log.responseBody = body.substring(0, maxLen) + '... (truncated)'
          }
        }
      } catch {
        // Ignore parse errors
      }

      this.events.emit({ type: 'network:response', data: log })
    })

    this.page.on('requestfailed', (request: Request) => {
      const log = this.requestMap.get(request)
      if (!log) return

      log.error = request.failure()?.errorText || 'Unknown error'

      const startTime = this.requestStartTimes.get(request)
      if (startTime) {
        log.duration = Date.now() - startTime
        this.requestStartTimes.delete(request)
      }

      this.events.emit({ type: 'network:error', data: log })
    })
  }

  private sanitizeData(data: string): string {
    try {
      const parsed = JSON.parse(data)
      const keys = this.options.sanitizeKeys
      const sanitized = JSON.parse(JSON.stringify(parsed), (key, value) => {
        if (typeof value === 'string' && keys.some(k => key.toLowerCase().includes(k))) {
          return '***REDACTED***'
        }
        return value
      })
      return JSON.stringify(sanitized)
    } catch {
      // Fallback regex replacement for non-JSON
      return data.replace(/"password":"[^"]*"/g, '"password":"***REDACTED***"')
    }
  }

  private sanitizeCookie(setCookie: string): string {
    const cookies = setCookie.split('\n')
    return cookies.map(cookie => {
      const match = cookie.match(/^([^=]+)=([^;]+)/)
      if (match) {
        const name = match[1]
        if (this.options.authCookieNames.includes(name.toLowerCase())) {
          return cookie.replace(match[2], '***REDACTED***')
        }
      }
      return cookie
    }).join('\n')
  }

  private pickReplayHeaders(headers: Record<string, string>): Record<string, string> {
    const keep = this.options.replayHeaders
    const selected: Record<string, string> = {}
    for (const [key, value] of Object.entries(headers)) {
      if (keep.includes(key.toLowerCase())) {
        selected[key] = value
      }
    }
    return selected
  }

  // ── Public API ──

  printLogs(title?: string): void {
    console.log(formatVerboseNetworkLogs(this.logs, title))
  }

  printFailedLogs(title?: string): void {
    console.log(formatFailedNetworkLogs(this.logs, title))
  }

  printMiniSummary(title?: string): void {
    const failed = this.getFailedLogs()
    const aggregated = this.getAggregatedLogs()
    console.log(formatMiniNetworkSummary(this.logs, failed, aggregated, title))
  }

  printAggregatedLogs(title?: string): void {
    console.log(formatAggregatedNetworkLogs(this.getAggregatedLogs(), title))
  }

  getLogs(): ApiRequestLog[] {
    return this.logs
  }

  getFailedLogs(): ApiRequestLog[] {
    return this.logs.filter(log =>
      log.error || (log.status && log.status >= 400)
    )
  }

  getAggregatedLogs(): Record<string, AggregatedRequestStats> {
    const aggregated: Record<string, { count: number; successCount: number; failureCount: number; totalDuration: number }> = {}

    for (const log of this.logs) {
      let pathname: string
      try {
        pathname = new URL(log.url, 'http://localhost').pathname
      } catch {
        pathname = log.url
      }
      const key = `${log.method} ${pathname}`

      if (!aggregated[key]) {
        aggregated[key] = { count: 0, successCount: 0, failureCount: 0, totalDuration: 0 }
      }

      aggregated[key].count++
      if (log.status && log.status >= 200 && log.status < 300) {
        aggregated[key].successCount++
      } else if ((log.status && log.status >= 400) || log.error) {
        aggregated[key].failureCount++
      }
      if (log.duration) {
        aggregated[key].totalDuration += log.duration
      }
    }

    const result: Record<string, AggregatedRequestStats> = {}
    for (const [key, value] of Object.entries(aggregated)) {
      result[key] = {
        count: value.count,
        successCount: value.successCount,
        failureCount: value.failureCount,
        avgDuration: value.totalDuration > 0 ? Math.round(value.totalDuration / value.count) : undefined,
      }
    }

    return result
  }

  findLogsByRequestId(requestId: string): ApiRequestLog[] {
    return this.logs.filter(log => log.requestId === requestId)
  }

  getLogsWithRequestId(): ApiRequestLog[] {
    return this.logs.filter(log => log.requestId)
  }

  exportToJson(): string {
    // Strip internal ID before export
    const exportLogs = this.logs.map(({ _internalId, ...rest }) => rest)
    return JSON.stringify(exportLogs, null, 2)
  }

  clearLogs(): void {
    this.logs = []
  }
}
