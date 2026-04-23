/**
 * Formatters - Pure functions for log output formatting
 *
 * Extracted from logger classes to enable testing and reuse.
 */

import * as path from 'path'
import type {
  ApiRequestLog,
  RouteChangeLog,
  ConsoleLogEntry,
  TestSummary,
  AggregatedRequestStats,
  DeduplicationStats,
} from '../types'

// ── Network Formatters ──

export function formatNetworkLog(log: ApiRequestLog): string {
  const parts: string[] = [`[${log.timestamp}] ${log.method} ${log.url}`]
  if (log.requestId) parts.push(`  Request ID: ${log.requestId}`)
  if (log.requestCookie) parts.push(`  Cookie: ${log.requestCookie}`)
  if (log.pageCookies) parts.push(`  Page Cookies: ${log.pageCookies}`)
  if (log.requestBody) parts.push(`  \u2192 Request: ${log.requestBody}`)

  if (log.status) {
    const icon = log.status >= 200 && log.status < 300 ? '\u2713' : '\u2717'
    parts.push(`  \u2190 Response: ${icon} ${log.status}${log.duration ? ` (${log.duration}ms)` : ''}`)
    if (log.responseSetCookie) parts.push(`  Set-Cookie: ${log.responseSetCookie}`)
    if (log.responseBody) {
      try {
        const parsed = JSON.parse(log.responseBody)
        const formatted = JSON.stringify(parsed, null, 2)
        parts.push(`    Body:\n${formatted.split('\n').join('\n    ')}`)
      } catch {
        parts.push(`    Body: ${log.responseBody}`)
      }
    }
  }

  if (log.error) {
    parts.push(`  \u2717 Error: ${log.error}${log.duration ? ` (${log.duration}ms)` : ''}`)
  }

  return parts.join('\n')
}

export function formatVerboseNetworkLogs(logs: ApiRequestLog[], title?: string): string {
  if (logs.length === 0) return '[Network] No API requests captured'

  const lines = [
    '\n' + '='.repeat(80),
    title || 'API Request Logs',
    '='.repeat(80),
  ]

  for (const log of logs) {
    lines.push('\n' + formatNetworkLog(log))
  }

  lines.push('\n' + '='.repeat(80))
  return lines.join('\n')
}

export function formatFailedNetworkLogs(logs: ApiRequestLog[], title?: string): string {
  const failed = logs.filter(log => log.error || (log.status && log.status >= 400))

  if (failed.length === 0) return '[Network] All API requests successful'

  const lines = [
    '\n' + '='.repeat(80),
    title || 'Failed API Requests',
    '='.repeat(80),
  ]

  for (const log of failed) {
    lines.push('\n' + formatNetworkLog(log))
  }

  lines.push('\n' + '='.repeat(80))
  return lines.join('\n')
}

export function formatMiniNetworkSummary(
  logs: ApiRequestLog[],
  failedLogs: ApiRequestLog[],
  aggregated: Record<string, AggregatedRequestStats>,
  title?: string
): string {
  const uniqueRequests = Object.keys(aggregated).length
  const lines = [`[Network] ${title || 'Summary'}: ${logs.length} requests (${uniqueRequests} unique), ${failedLogs.length} failed`]

  if (failedLogs.length > 0) {
    const showCount = Math.min(failedLogs.length, 5)
    if (failedLogs.length > 5) {
      lines.push(`  (First 5 of ${failedLogs.length} failed requests)`)
    }
    failedLogs.slice(0, showCount).forEach(f => {
      const status = f.status || (f.error ? 'ERR' : '?')
      lines.push(`  ${f.method} ${f.url} \u2192 ${status}`)
    })
  }

  return lines.join('\n')
}

export function formatAggregatedNetworkLogs(
  aggregated: Record<string, AggregatedRequestStats>,
  title?: string
): string {
  const entries = Object.entries(aggregated).sort((a, b) => b[1].count - a[1].count)

  const lines = [
    '\n' + '='.repeat(80),
    title || 'Aggregated API Requests',
    '='.repeat(80),
  ]

  for (const [key, stats] of entries) {
    const icon = stats.failureCount === 0 ? '\u2713' : '\u2717'
    const durationStr = stats.avgDuration ? ` (${stats.avgDuration}ms avg)` : ''
    lines.push(`  ${icon} ${key}: ${stats.count}x [${stats.successCount} success, ${stats.failureCount} failed]${durationStr}`)
  }

  lines.push('='.repeat(80))
  return lines.join('\n')
}

// ── Route Formatters ──

export function getTriggerIcon(trigger?: string): string {
  switch (trigger) {
    case 'goto': return '\u2192'
    case 'redirect': return '\u21DD'
    case 'back_forward': return '\u2194'
    default: return '\u2192'
  }
}

export function formatRouteChange(log: RouteChangeLog, stepNum: number, isRedirect?: boolean): string {
  const icon = getTriggerIcon(log.trigger)
  const lines = [`\n[${stepNum}] ${log.timestamp}`]

  if (log.title) {
    lines.push(`  ${icon} ${log.url}`)
    lines.push(`     Title: "${log.title}"`)
  } else {
    lines.push(`  ${icon} ${log.url}`)
  }

  if (log.trigger) {
    lines.push(`     Trigger: ${log.trigger}`)
  }

  if (isRedirect) {
    lines.push('     \u26A0\uFE0F  Possible auto-redirect detected')
  }

  return lines.join('\n')
}

export function formatVerboseRouteLogs(routeLogs: RouteChangeLog[], redirectDetector?: (from: string, to: string) => boolean, title?: string): string {
  if (routeLogs.length === 0) return '[Route] No route changes captured'

  const lines = [
    '\n' + '='.repeat(80),
    title || 'Route Changes',
    '='.repeat(80),
  ]

  for (let i = 0; i < routeLogs.length; i++) {
    const log = routeLogs[i]
    let isRedirect = false
    if (i > 0 && redirectDetector) {
      isRedirect = redirectDetector(routeLogs[i - 1].url, log.url)
    }
    lines.push(formatRouteChange(log, i + 1, isRedirect))
  }

  lines.push('\n' + '='.repeat(80))
  return lines.join('\n')
}

export function formatMiniRouteSummary(routeLogs: RouteChangeLog[], redirectCount: number, title?: string): string {
  const lines = [`[Route] ${title || 'Summary'}: ${routeLogs.length} changes${redirectCount > 0 ? ` (${redirectCount} possible redirects)` : ''}`]

  if (routeLogs.length > 0) {
    const recent = routeLogs.slice(-3)
    recent.forEach((log, idx) => {
      const icon = getTriggerIcon(log.trigger)
      const prefix = routeLogs.length > 3
        ? `... +${routeLogs.length - 3} more, then `
        : `${routeLogs.length - recent.length + idx + 1}. `
      lines.push(`  ${prefix}${icon} ${shortenUrl(log.url)}`)
    })
  }

  return lines.join('\n')
}

function shortenUrl(url: string): string {
  try {
    const urlObj = new URL(url)
    const segments = urlObj.pathname.split('/').filter(s => s)
    if (segments.length > 2) {
      return '.../' + segments.slice(-2).join('/')
    }
    return urlObj.pathname || url
  } catch {
    return url.length > 50 ? url.substring(0, 50) + '...' : url
  }
}

// ── Console Formatters ──

export function formatConsoleLogLine(entry: ConsoleLogEntry, isDuplicate: boolean, isFiltered: boolean): string {
  const dedupMarker = isDuplicate ? ' [DUPLICATE]' : ''
  const filterMarker = isFiltered ? ' [FILTERED]' : ''
  return `[${entry.timestamp}] [${entry.type.toUpperCase()}]${dedupMarker}${filterMarker} ${entry.text}${entry.location ? ` (${entry.location})` : ''}\n`
}

export function formatConsoleQuietSummary(
  errors: number,
  warnings: number,
  dedupStats: DeduplicationStats,
  filteredCount: number,
  compactMode: boolean,
  logFilePath?: string
): string {
  const opt = [
    dedupStats.duplicatesFiltered && `${dedupStats.duplicatesFiltered}d`,
    filteredCount && `${filteredCount}f`
  ].filter(Boolean).join(',')

  if (compactMode) {
    return `[Con] ${errors}e/${warnings}w${opt ? ` (${opt})` : ''}`
  }

  const relativePath = logFilePath ? path.relative(process.cwd(), logFilePath) : ''
  return `[Con] ${errors}e/${warnings}w${opt ? ` (${opt})` : ''}${relativePath ? ` \u2192 ${relativePath}` : ''}`
}

export function formatConsoleVerboseSummary(
  errors: number,
  warnings: number,
  dedupStats: DeduplicationStats,
  filteredCount: number,
  logFilePath: string
): string {
  const lines = [
    `[ConsoleLogger] Logs written to: ${logFilePath}`,
    `  Absolute path: ${path.resolve(logFilePath)}`,
    `[ConsoleLogger] Summary: ${errors} errors, ${warnings} warnings`,
  ]

  if (dedupStats.duplicatesFiltered > 0) {
    lines.push(`[ConsoleLogger] Deduplication: ${dedupStats.duplicatesFiltered} duplicates filtered`)
  }
  if (filteredCount > 0) {
    lines.push(`[ConsoleLogger] Filtering: ${filteredCount} messages filtered`)
  }

  return lines.join('\n')
}

// ── Test Code Formatters ──

export function formatTestCodeLogLine(entry: { timestamp: string; type: string; message: string; sourceLocation?: string }): string {
  const location = entry.sourceLocation ? ` (${entry.sourceLocation})` : ''
  return `[${entry.timestamp}] [${entry.type.toUpperCase()}] [TEST_CODE] ${entry.message}${location}`
}

// ── Unified Summary Formatters ──

export function formatVerboseSummary(title: string, summary: TestSummary, consoleLogFile: string): string {
  return [
    `\n=== ${title} ===`,
    `\nConsole logs: ${consoleLogFile}`,
    `\n[Summary]`,
    `  Network requests: ${summary.networkRequests}`,
    `  Failed requests: ${summary.failedRequests}`,
    `  Route changes: ${summary.routeChanges}`,
    `  Possible redirects: ${summary.possibleRedirects}`,
    `  Console logs: ${summary.consoleLogs}`,
    `  Console errors: ${summary.consoleErrors}`,
    `  Console warnings: ${summary.consoleWarnings}`,
    `  Test code logs: ${summary.testCodeLogs}`,
    `  Test code errors: ${summary.testCodeErrors}`,
    `  Test code warnings: ${summary.testCodeWarnings}`,
  ].join('\n')
}

export function formatMiniSummary(title: string | undefined, summary: TestSummary, compactMode: boolean, logFilePath?: string): string {
  const label = title || 'Uni'

  if (compactMode) {
    return `[${label}] ${summary.networkRequests}r/${summary.failedRequests}f ${summary.consoleErrors}e/${summary.consoleWarnings}w ${summary.routeChanges}rt/${summary.testCodeLogs}tl`
  }

  const relativePath = logFilePath ? path.relative(process.cwd(), logFilePath) : ''
  return `[Uni] ${summary.networkRequests}r/${summary.failedRequests}f ${summary.consoleErrors}e/${summary.consoleWarnings}w ${summary.routeChanges}rt/${summary.testCodeLogs}tl${relativePath ? ` \u2192 ${relativePath}` : ''}`
}
