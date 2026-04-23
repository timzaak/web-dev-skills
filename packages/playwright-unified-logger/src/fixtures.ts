/**
 * Playwright Fixture exports
 *
 * Pre-built test.extend() fixtures for zero-config usage.
 *
 * Usage:
 * ```typescript
 * // Zero-config
 * import { test, expect } from 'playwright-unified-logger/fixtures'
 *
 * // Custom config
 * import { createLoggerFixture } from 'playwright-unified-logger/fixtures'
 * const test = createLoggerFixture({ logLevel: 'verbose' })
 * ```
 */

import { test as base } from '@playwright/test'
import { UnifiedLogger } from './core/unified-logger'
import type { UnifiedLoggerConfig } from './types'

export interface LoggerFixtures {
  unifiedLogger: UnifiedLogger
}

/**
 * Create a Playwright test fixture with UnifiedLogger.
 *
 * The logger is automatically finalized after each test,
 * printing a summary and writing log files.
 */
export function createLoggerFixture(config?: UnifiedLoggerConfig) {
  return base.extend<LoggerFixtures>({
    unifiedLogger: async ({ page }, use, testInfo) => {
      const logger = new UnifiedLogger(page, testInfo.title, config)
      await use(logger)
      logger.printSummary(`[${testInfo.title}] Summary`)
      await logger.finalize()
    },
  })
}

/** Default test fixture with zero config */
export const test = createLoggerFixture()

/** Re-export expect from Playwright */
export { expect } from '@playwright/test'
