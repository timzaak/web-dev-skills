/**
 * UnifiedLogger - Coordinator for all sub-loggers
 *
 * Integrates NetworkLogger, ConsoleLogger, RouteLogger, and TestCodeLogger.
 * All logs are written to files via WriteBuffer for efficient I/O.
 *
 * Usage:
 * ```typescript
 * import { UnifiedLogger } from 'playwright-unified-logger'
 *
 * const logger = new UnifiedLogger(page, testInfo.title)
 * // ... test logic ...
 * logger.printSummary('Test Summary')
 * await logger.finalize()
 * ```
 */

import { Page } from '@playwright/test'
import * as fs from 'fs'
import type { UnifiedLoggerConfig, TestLogs, TestSummary } from '../types'
import { resolveConfig } from '../config'
import { LoggerEventBus } from './event-bus'
import { NetworkLogger } from '../loggers/network-logger'
import { ConsoleLogger } from '../loggers/console-logger'
import { RouteLogger } from '../loggers/route-logger'
import { TestCodeLogger } from '../loggers/test-code-logger'
import { formatVerboseSummary, formatMiniSummary } from '../output/formatters'

export class UnifiedLogger {
  public network: NetworkLogger
  public browserConsole: ConsoleLogger
  public route: RouteLogger
  public testCode: TestCodeLogger
  public events: LoggerEventBus

  private config: ReturnType<typeof resolveConfig>
  private quietMode: boolean
  private compactMode: boolean

  constructor(page: Page, testTitle: string, config?: UnifiedLoggerConfig | boolean) {
    // Backward compatibility: third arg was boolean quietMode
    if (typeof config === 'boolean') {
      config = config ? { logLevel: 'silent' } : { logLevel: 'verbose' }
    }

    this.config = resolveConfig(config)
    this.quietMode = this.config.quietMode
    this.compactMode = this.config.compactMode ?? false
    this.events = new LoggerEventBus()

    this.network = new NetworkLogger(page, this.quietMode, this.events, this.config.network)
    this.browserConsole = new ConsoleLogger(
      page, testTitle, this.quietMode,
      this.config.deduplication !== false,
      this.config.console,
      this.compactMode,
      this.config.outputDir,
      this.events
    )
    this.route = new RouteLogger(page, this.quietMode, this.events, this.config.route)
    this.testCode = new TestCodeLogger(
      this.browserConsole.getLogFilePath(),
      this.config.testCode?.enabled !== false,
      this.events,
      this.config.testCode
    )
  }

  /**
   * @deprecated Use `browserConsole` instead. The `console` name shadows the global.
   */
  get console(): ConsoleLogger {
    return this.browserConsole
  }

  /**
   * Finalize all loggers, write files, and return log paths + summary.
   * Must be called in test teardown (usually fixture afterUse).
   */
  async finalize(): Promise<TestLogs> {
    // Restore console before finalizing sub-loggers
    this.testCode.restoreConsole()
    await this.browserConsole.finalize()
    await this.testCode.finalize()

    const baseName = this.browserConsole.getLogFilePath().replace(/\.log$/, '')

    // Save network logs as JSON
    const networkLogFile = `${baseName}-network.json`
    fs.writeFileSync(networkLogFile, this.network.exportToJson())

    // Save route logs as JSON
    const routeLogFile = `${baseName}-route.json`
    fs.writeFileSync(routeLogFile, this.route.exportToJson())

    const summary = this.computeSummary()

    return {
      networkLogs: networkLogFile,
      consoleLogs: this.browserConsole.getLogFilePath(),
      routeLogs: routeLogFile,
      testCodeLogs: this.testCode.getLogFilePath() || '',
      timestamp: new Date().toISOString(),
      summary,
    }
  }

  /**
   * Print log summary based on current log level.
   */
  printSummary(title: string): void {
    if (this.quietMode) {
      this.printMiniSummary(title)
      return
    }
    this.printVerboseSummary(title)
  }

  private printVerboseSummary(title: string): void {
    const summary = this.computeSummary()
    console.log(formatVerboseSummary(title, summary, this.browserConsole.getLogFilePath()))
    this.network.printLogs(title)
    this.route.printRouteChanges(title)
  }

  private printMiniSummary(title?: string): void {
    const summary = this.computeSummary()
    console.log(formatMiniSummary(title, summary, this.compactMode, this.browserConsole.getLogFilePath()))
  }

  /**
   * Print only failed requests
   */
  printFailedLogs(title: string): void {
    this.network.printFailedLogs(title)
  }

  /**
   * Print route changes
   */
  printRouteChanges(title?: string): void {
    this.route.printRouteChanges(title)
  }

  private computeSummary(): TestSummary {
    const consoleLogs = this.browserConsole.getLogs()
    const routeAnalysis = this.route.analyzeRoutePattern()

    return {
      networkRequests: this.network.getLogs().length,
      failedRequests: this.network.getFailedLogs().length,
      routeChanges: routeAnalysis.totalChanges,
      possibleRedirects: routeAnalysis.possibleRedirects,
      consoleLogs: consoleLogs.length,
      consoleErrors: consoleLogs.filter(l => l.type === 'error').length,
      consoleWarnings: consoleLogs.filter(l => l.type === 'warning').length,
      testCodeLogs: this.testCode.getLogs().length,
      testCodeErrors: this.testCode.getErrorLogs().length,
      testCodeWarnings: this.testCode.getWarningLogs().length,
    }
  }
}
