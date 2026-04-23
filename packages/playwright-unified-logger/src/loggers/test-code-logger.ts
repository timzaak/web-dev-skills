/**
 * Test Code Logger - Node.js test code console capture
 *
 * Intercepts console.log/warn/error/info in Node.js test code.
 * Guards against double-initialization for parallel test safety.
 */

import * as path from 'path'
import type { TestCodeLogEntry, TestCodeLoggerOptions } from '../types'
import { LoggerEventBus } from '../core/event-bus'
import { WriteBuffer } from '../output/write-buffer'
import { formatTestCodeLogLine } from '../output/formatters'

type ConsoleMethod = 'log' | 'info' | 'warn' | 'error'

/** Default patterns for source file location extraction */
const DEFAULT_SOURCE_FILE_PATTERNS: RegExp[] = [
  /\(([^:]+\.e2e\.ts):(\d+):\d+\)/,
  /\(([^:]+\.spec\.ts):(\d+):\d+\)/,
  /at\s+([^:]+\.e2e\.ts):(\d+)/,
  /at\s+([^:]+\.spec\.ts):(\d+)/,
]

/**
 * Format a single argument to string
 */
function formatArgument(arg: unknown): string {
  if (typeof arg === 'string') return arg
  if (arg instanceof Error) return `${arg.name}: ${arg.message}`
  if (arg === null) return 'null'
  if (arg === undefined) return 'undefined'
  if (typeof arg === 'object') {
    try {
      return JSON.stringify(arg, null, 2)
    } catch {
      return String(arg)
    }
  }
  return String(arg)
}

/** Global guard to prevent double-initialization across parallel tests */
let globalInitialized = false

export class TestCodeLogger {
  private logs: TestCodeLogEntry[] = []
  private writeBuffer: WriteBuffer | null = null
  private enabled: boolean
  private initialized = false
  private originalConsole = new Map<ConsoleMethod, typeof console.log>()
  private sourceFilePatterns: RegExp[]
  private events: LoggerEventBus

  constructor(logFile: string, enabled: boolean, events: LoggerEventBus, options?: TestCodeLoggerOptions) {
    this.enabled = enabled
    this.events = events
    this.sourceFilePatterns = options?.sourceFilePatterns ?? DEFAULT_SOURCE_FILE_PATTERNS

    if (this.enabled && !globalInitialized) {
      this.writeBuffer = new WriteBuffer(logFile)
      this.initialize()
    }
  }

  private initialize(): void {
    if (this.initialized || !this.enabled || globalInitialized) return

    globalInitialized = true
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

  private captureLog(type: ConsoleMethod, args: unknown[]): void {
    if (!this.enabled) return

    const entry: TestCodeLogEntry = {
      timestamp: new Date().toISOString(),
      type,
      message: args.map(formatArgument).join(' '),
      sourceLocation: this.extractSourceLocation(),
    }

    this.logs.push(entry)
    if (this.writeBuffer) {
      this.writeBuffer.append(formatTestCodeLogLine(entry) + '\n')
    }
    this.events.emit({ type: 'testcode:log', data: entry })
  }

  private extractSourceLocation(): string | undefined {
    const stack = new Error().stack
    if (!stack) return undefined

    const lines = stack.split('\n')
    for (let i = 4; i < lines.length; i++) {
      for (const pattern of this.sourceFilePatterns) {
        const match = lines[i].match(pattern)
        if (match) {
          return `${path.basename(match[1])}:${match[2]}`
        }
      }
    }

    return undefined
  }

  /**
   * Restore original console methods (call in test teardown)
   */
  restoreConsole(): void {
    if (!this.initialized) return

    for (const [method, originalFn] of this.originalConsole.entries()) {
      console[method] = originalFn
    }

    this.initialized = false
    globalInitialized = false
  }

  async finalize(): Promise<void> {
    if (this.writeBuffer) {
      await this.writeBuffer.finalize()
    }
  }

  getLogFilePath(): string | undefined {
    return this.writeBuffer?.getFilePath()
  }

  getLogs(): TestCodeLogEntry[] {
    return this.logs
  }

  getLogsByType(type: ConsoleMethod): TestCodeLogEntry[] {
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
