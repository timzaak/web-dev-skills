/**
 * LoggerEventBus - Typed event emitter for logger extensibility
 *
 * Allows consumers to subscribe to log events for custom handling
 * (e.g., sending to external monitoring, custom formatting).
 *
 * Usage:
 * ```typescript
 * logger.events.on('network:error', (event) => {
 *   // custom handling
 * })
 * ```
 */

import type {
  LoggerEvent,
  LoggerEventHandler,
} from '../types'

type HandlerMap = {
  'network:request': LoggerEventHandler<'network:request'>
  'network:response': LoggerEventHandler<'network:response'>
  'network:error': LoggerEventHandler<'network:error'>
  'console:message': LoggerEventHandler<'console:message'>
  'console:error': LoggerEventHandler<'console:error'>
  'route:change': LoggerEventHandler<'route:change'>
  'testcode:log': LoggerEventHandler<'testcode:log'>
}

export class LoggerEventBus {
  private handlers = new Map<string, Set<(event: LoggerEvent) => void>>()

  /**
   * Subscribe to a logger event.
   * Returns an unsubscribe function.
   */
  on<T extends keyof HandlerMap>(
    type: T,
    handler: HandlerMap[T]
  ): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set())
    }
    const set = this.handlers.get(type)!
    set.add(handler as (event: LoggerEvent) => void)

    return () => {
      set.delete(handler as (event: LoggerEvent) => void)
      if (set.size === 0) {
        this.handlers.delete(type)
      }
    }
  }

  /**
   * Emit an event to all subscribers
   */
  emit(event: LoggerEvent): void {
    const set = this.handlers.get(event.type)
    if (set) {
      for (const handler of set) {
        try {
          handler(event)
        } catch {
          // Swallow errors in event handlers to avoid breaking the logger
        }
      }
    }
  }

  /**
   * Remove all handlers
   */
  clear(): void {
    this.handlers.clear()
  }
}
