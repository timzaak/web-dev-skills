/**
 * Playwright Unified Logger
 *
 * Unified logging for Playwright E2E tests - captures network, console,
 * route changes and test code logs with efficient buffered file I/O.
 *
 * Usage:
 * ```typescript
 * import { UnifiedLogger } from 'playwright-unified-logger'
 *
 * const logger = new UnifiedLogger(page, 'my-test')
 * // ... test logic ...
 * logger.printSummary('Test Summary')
 * await logger.finalize()
 * ```
 */

// Core class
export { UnifiedLogger } from './core/unified-logger'

// Sub-loggers (can be used independently)
export { NetworkLogger } from './loggers/network-logger'
export { ConsoleLogger } from './loggers/console-logger'
export { RouteLogger } from './loggers/route-logger'
export { TestCodeLogger } from './loggers/test-code-logger'

// Event bus
export { LoggerEventBus } from './core/event-bus'

// Configuration
export { resolveConfig, isSilentMode, isVerboseMode, isMiniMode, formatLogPath } from './config'

// All types
export type {
  LogLevel,
  TestLogs,
  TestSummary,
  UnifiedLoggerConfig,
  NetworkLoggerOptions,
  ConsoleLoggerOptions,
  RouteLoggerOptions,
  TestCodeLoggerOptions,
  RouteAnalysis,
  AggregatedRequestStats,
  DeduplicationStats,
  LoggerEvent,
  LoggerEventType,
  LoggerEventHandler,
  ApiRequestLog,
  ConsoleLogEntry,
  RouteChangeLog,
  TestCodeLogEntry,
} from './types'
