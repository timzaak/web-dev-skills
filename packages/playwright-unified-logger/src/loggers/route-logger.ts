/**
 * Route Logger - SPA route change capture
 *
 * Configurable redirect detection and route analysis.
 */

import { Page, Frame } from '@playwright/test'
import type { RouteChangeLog, RouteLoggerOptions, RouteAnalysis } from '../types'
import { LoggerEventBus } from '../core/event-bus'
import { formatVerboseRouteLogs, formatMiniRouteSummary } from '../output/formatters'

/** Default redirect detector: login/register pages to dashboard/manage pages */
function defaultRedirectDetector(fromUrl: string, toUrl: string): boolean {
  const isFromAuth = fromUrl.includes('/login') || fromUrl.includes('/register')
  const isToDashboard = toUrl.includes('/dashboard') || toUrl.includes('/manage')
  return isFromAuth && isToDashboard
}

function defaultRouteAnalyzer(logs: RouteChangeLog[], redirectDetector: (from: string, to: string) => boolean): RouteAnalysis {
  const authPages = logs.filter(log =>
    log.url.includes('/login') || log.url.includes('/register')
  ).length

  const dashboardPages = logs.filter(log =>
    log.url.includes('/dashboard')
  ).length

  let possibleRedirects = 0
  for (let i = 1; i < logs.length; i++) {
    if (redirectDetector(logs[i - 1].url, logs[i].url)) {
      possibleRedirects++
    }
  }

  return {
    totalChanges: logs.length,
    possibleRedirects,
    authPages,
    dashboardPages,
    lastUrl: logs.length > 0 ? logs[logs.length - 1].url : '',
  }
}

export class RouteLogger {
  private routeLogs: RouteChangeLog[] = []
  private page: Page
  private quietMode: boolean
  private lastUrl: string = ''
  private events: LoggerEventBus
  private redirectDetector: (fromUrl: string, toUrl: string) => boolean
  private routeAnalyzer: (logs: RouteChangeLog[]) => RouteAnalysis

  constructor(
    page: Page,
    quietMode: boolean,
    events: LoggerEventBus,
    options?: RouteLoggerOptions
  ) {
    this.page = page
    this.quietMode = quietMode
    this.events = events
    this.redirectDetector = options?.redirectDetector ?? defaultRedirectDetector
    this.routeAnalyzer = options?.routeAnalyzer
      ?? ((logs) => defaultRouteAnalyzer(logs, this.redirectDetector))

    this.attachListeners()
  }

  private detectTriggerType(url: string): 'goto' | 'redirect' | 'back_forward' | 'unknown' {
    if (url.includes('/redirect') || url.includes('?redirect')) {
      return 'redirect'
    }
    return 'unknown'
  }

  private attachListeners(): void {
    this.page.on('framenavigated', async (frame: Frame) => {
      if (frame !== this.page.mainFrame()) return

      const url = frame.url()
      if (url === this.lastUrl) return

      const title = await frame.title().catch(() => '')
      const log: RouteChangeLog = {
        timestamp: new Date().toISOString(),
        url,
        title: title || undefined,
        trigger: this.detectTriggerType(url),
      }

      this.routeLogs.push(log)
      this.lastUrl = url

      if (this.quietMode) {
        // Quiet mode output handled by printMiniSummary in UnifiedLogger
      }

      this.events.emit({ type: 'route:change', data: log })
    })
  }

  printRouteChanges(title?: string): void {
    console.log(formatVerboseRouteLogs(this.routeLogs, this.redirectDetector, title))
  }

  printMiniSummary(title?: string): void {
    const redirectCount = this.detectRedirectCount()
    console.log(formatMiniRouteSummary(this.routeLogs, redirectCount, title))
  }

  private detectRedirectCount(): number {
    let count = 0
    for (let i = 1; i < this.routeLogs.length; i++) {
      if (this.redirectDetector(this.routeLogs[i - 1].url, this.routeLogs[i].url)) {
        count++
      }
    }
    return count
  }

  analyzeRoutePattern(): RouteAnalysis {
    return this.routeAnalyzer(this.routeLogs)
  }

  getRouteLogs(): RouteChangeLog[] {
    return this.routeLogs
  }

  exportToJson(): string {
    return JSON.stringify(this.routeLogs, null, 2)
  }

  clearRouteLogs(): void {
    this.routeLogs = []
    this.lastUrl = ''
  }
}
