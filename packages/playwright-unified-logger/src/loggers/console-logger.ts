/**
 * Console Logger - Browser console message capture
 *
 * Uses WriteBuffer for efficient file I/O.
 * Filter patterns are fully configurable.
 */

import { Page, ConsoleMessage } from '@playwright/test'
import type { ConsoleLogEntry, ConsoleLoggerOptions, DeduplicationStats } from '../types'
import { LoggerEventBus } from '../core/event-bus'
import { WriteBuffer } from '../output/write-buffer'
import { formatConsoleLogLine, formatConsoleQuietSummary, formatConsoleVerboseSummary } from '../output/formatters'

/** Default filter patterns for harmless development environment noise */
const DEFAULT_FILTER_PATTERNS: RegExp[] = [
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
  private writeBuffer: WriteBuffer
  private quietMode: boolean
  private compactMode: boolean
  private deduplicationEnabled: boolean
  private filteringEnabled: boolean
  private filterPatterns: RegExp[]
  private seenLogs = new Set<string>()
  private filteredCount = 0
  private events: LoggerEventBus

  constructor(
    page: Page,
    testTitle: string,
    quietMode: boolean,
    deduplicationEnabled: boolean,
    options: ConsoleLoggerOptions | undefined,
    compactMode: boolean,
    outputDir: string,
    events: LoggerEventBus
  ) {
    this.page = page
    this.quietMode = quietMode
    this.compactMode = compactMode
    this.deduplicationEnabled = deduplicationEnabled
    this.filteringEnabled = options?.filteringEnabled ?? true
    this.filterPatterns = options?.filterPatterns ?? DEFAULT_FILTER_PATTERNS
    this.events = events

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const safeTestTitle = testTitle.replace(/[^a-zA-Z0-9\-_]/g, '_')
    const runId = process.env.UNIFIED_RUN_ID || process.env.DEMO_RUN_ID || 'no-run-id'
    const logFilePath = `${outputDir}/${runId}-${safeTestTitle}-${timestamp}.log`

    this.writeBuffer = new WriteBuffer(logFilePath)
    this.attachListeners()
  }

  private shouldFilter(entry: ConsoleLogEntry): boolean {
    if (!this.filteringEnabled || entry.type === 'error') {
      return false
    }
    return this.filterPatterns.some(pattern => pattern.test(entry.text))
  }

  private isDuplicate(entry: ConsoleLogEntry): boolean {
    if (!this.deduplicationEnabled) return false
    const logKey = `${entry.type}:${entry.text}`
    if (this.seenLogs.has(logKey)) return true
    this.seenLogs.add(logKey)
    return false
  }

  private attachListeners(): void {
    this.page.on('console', (msg: ConsoleMessage) => {
      const entry: ConsoleLogEntry = {
        timestamp: new Date().toISOString(),
        type: msg.type(),
        text: msg.text(),
        location: msg.location()?.url,
      }

      if (this.shouldFilter(entry)) {
        this.filteredCount++
        this.writeBuffer.append(formatConsoleLogLine(entry, false, true))
        return
      }

      const isDuplicate = this.isDuplicate(entry)
      if (!isDuplicate) {
        this.logs.push(entry)
      }
      this.writeBuffer.append(formatConsoleLogLine(entry, isDuplicate, false))

      const eventType = entry.type === 'error' ? 'console:error' : 'console:message'
      this.events.emit({ type: eventType, data: entry })
    })

    this.page.on('pageerror', (error: Error) => {
      const isUnhandledRejection = error.message.includes('UnhandledPromiseRejection')
      const entry: ConsoleLogEntry = {
        timestamp: new Date().toISOString(),
        type: isUnhandledRejection ? 'warning' : 'error',
        text: isUnhandledRejection
          ? error.message
          : `${error.message}\n${error.stack}`,
      }

      // Skip deduplication for unhandled rejections (always record them)
      if (!isUnhandledRejection) {
        const isDuplicate = this.isDuplicate(entry)
        if (!isDuplicate) {
          this.logs.push(entry)
        }
        this.writeBuffer.append(formatConsoleLogLine(entry, isDuplicate, false))
      } else {
        this.logs.push(entry)
        this.writeBuffer.append(formatConsoleLogLine(entry, false, false))
      }

      this.events.emit({ type: 'console:error', data: entry })
    })
  }

  async finalize(): Promise<void> {
    await this.writeBuffer.finalize()

    const summary = {
      totalLogs: this.logs.length,
      errors: this.logs.filter(l => l.type === 'error').length,
      warnings: this.logs.filter(l => l.type === 'warning').length,
    }
    const dedupStats = this.getDeduplicationStats()

    if (this.quietMode) {
      console.log(formatConsoleQuietSummary(
        summary.errors, summary.warnings, dedupStats, this.filteredCount,
        this.compactMode, this.writeBuffer.getFilePath()
      ))
    } else {
      console.log(formatConsoleVerboseSummary(
        summary.errors, summary.warnings, dedupStats, this.filteredCount,
        this.writeBuffer.getFilePath()
      ))
    }
  }

  getLogFilePath(): string {
    return this.writeBuffer.getFilePath()
  }

  /** @deprecated Use getLogFilePath() instead */
  get logFile(): string {
    return this.writeBuffer.getFilePath()
  }

  getDeduplicationStats(): DeduplicationStats {
    if (!this.deduplicationEnabled) {
      return { duplicatesFiltered: 0, uniqueLogs: this.logs.length }
    }
    return {
      duplicatesFiltered: Math.max(0, this.seenLogs.size - this.logs.length),
      uniqueLogs: this.logs.length,
    }
  }

  getLogs(): ConsoleLogEntry[] {
    return this.logs
  }

  clearLogs(): void {
    this.logs = []
  }
}
