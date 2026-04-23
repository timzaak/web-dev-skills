/**
 * Configuration - Merges programmatic config with environment variables
 *
 * Priority: programmatic config > environment variables > defaults
 */

import * as path from 'path'
import type { LogLevel, UnifiedLoggerConfig } from './types'

/** Resolve env var with dual prefix support (new UNIFIED_LOG_* and legacy DEMO_LOG_*) */
function env(key: string, fallback: string): string {
  return process.env[`UNIFIED_LOG_${key}`] || process.env[`DEMO_LOG_${key}`] || fallback
}

/**
 * Resolve the effective configuration by merging programmatic config with env vars.
 */
export function resolveConfig(overrides?: UnifiedLoggerConfig): UnifiedLoggerConfig & {
  quietMode: boolean
  outputDir: string
} {
  const logLevel = (overrides?.logLevel ?? env('LEVEL', 'mini')) as LogLevel
  const quietMode = logLevel === 'mini' || logLevel === 'silent'

  return {
    logLevel,
    compactMode: overrides?.compactMode ?? (env('COMPACT', 'false') === 'true'),
    outputDir: overrides?.outputDir ?? path.resolve(process.cwd(), env('OUTPUT_DIR', 'test-results/unified-logs')),
    deduplication: overrides?.deduplication ?? (env('DEDUP', 'true') !== 'false'),
    aggregation: overrides?.aggregation ?? (env('AGGREGATE', 'true') !== 'false'),
    quietMode,
    network: overrides?.network,
    console: overrides?.console,
    route: overrides?.route,
    testCode: overrides?.testCode,
  }
}

/**
 * Whether to suppress all console output
 */
export function isSilentMode(config?: UnifiedLoggerConfig): boolean {
  const level = config?.logLevel ?? env('LEVEL', 'mini')
  return level === 'silent'
}

/**
 * Whether verbose output is enabled
 */
export function isVerboseMode(config?: UnifiedLoggerConfig): boolean {
  const level = config?.logLevel ?? env('LEVEL', 'mini')
  return level === 'verbose'
}

/**
 * Whether mini output mode is active (default)
 */
export function isMiniMode(config?: UnifiedLoggerConfig): boolean {
  const level = config?.logLevel ?? env('LEVEL', 'mini')
  return !level || level === 'mini'
}

/**
 * Format a log file path for display
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
    display: `[${projectName}] ${relativePath}\n  Full: ${absolutePath}`,
  }
}
