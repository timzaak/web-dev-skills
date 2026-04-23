/**
 * WriteBuffer - Buffered file writer
 *
 * Collects log lines in memory and flushes to disk periodically
 * and on finalize(). Replaces per-event fs.appendFile calls.
 */

import * as fs from 'fs/promises'
import * as path from 'path'

export class WriteBuffer {
  private buffer: string[] = []
  private flushTimer: ReturnType<typeof setTimeout> | null = null
  private dirCreated = false
  private readonly flushIntervalMs: number

  constructor(
    private readonly filePath: string,
    flushIntervalMs: number = 500
  ) {
    this.flushIntervalMs = flushIntervalMs
  }

  /**
   * Append a log line to the buffer (synchronous, fast)
   */
  append(line: string): void {
    this.buffer.push(line)
    if (!this.flushTimer) {
      this.flushTimer = setTimeout(() => {
        this.flushTimer = null
        this.flush().catch(() => { /* silent - flush on finalize */ })
      }, this.flushIntervalMs)
    }
  }

  /**
   * Flush buffered content to disk
   */
  async flush(): Promise<void> {
    if (this.buffer.length === 0) return
    const content = this.buffer.join('')
    this.buffer = []

    try {
      if (!this.dirCreated) {
        await fs.mkdir(path.dirname(this.filePath), { recursive: true })
        this.dirCreated = true
      }
      await fs.appendFile(this.filePath, content)
    } catch {
      // Silent failure to avoid infinite recursion in console interception
    }
  }

  /**
   * Finalize the buffer - flush any remaining content and stop timer
   */
  async finalize(): Promise<void> {
    if (this.flushTimer) {
      clearTimeout(this.flushTimer)
      this.flushTimer = null
    }
    await this.flush()
  }

  /**
   * Get the output file path
   */
  getFilePath(): string {
    return this.filePath
  }
}
