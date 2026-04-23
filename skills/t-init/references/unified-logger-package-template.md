# Playwright Unified Logger 包模板

本文件包含 `packages/playwright-unified-logger/` 独立 npm 包的文件结构和 API 说明。
这是一个通用的 Playwright E2E 测试日志库，通过 monorepo workspace 引用。

包名：`playwright-unified-logger`

---

## 文件结构

```
packages/playwright-unified-logger/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts                    # 公共导出
│   ├── types.ts                    # 所有共享类型和接口
│   ├── config.ts                   # 配置解析（编程 + 环境变量）
│   ├── fixtures.ts                 # Playwright fixture 导出
│   ├── core/
│   │   ├── unified-logger.ts       # 协调器
│   │   └── event-bus.ts            # 事件总线（扩展机制）
│   ├── loggers/
│   │   ├── network-logger.ts       # 网络捕获
│   │   ├── console-logger.ts       # 浏览器控制台
│   │   ├── route-logger.ts         # 路由追踪
│   │   └── test-code-logger.ts     # 测试代码日志
│   └── output/
│       ├── write-buffer.ts         # 缓冲文件写入
│       └── formatters.ts           # 输出格式化函数
```

所有源文件内容以 `packages/playwright-unified-logger/src/` 下的实际文件为准。

---

## API 概览

### 核心类

```typescript
import { UnifiedLogger } from 'playwright-unified-logger'

// 基础用法（与旧版兼容）
const logger = new UnifiedLogger(page, testTitle)
logger.printSummary('Test Summary')
await logger.finalize()

// 编程配置
const logger = new UnifiedLogger(page, testTitle, {
  logLevel: 'verbose',
  network: { urlFilter: url => url.includes('/api/') },
  console: { filterPatterns: [/HMR/i, /React DevTools/i] },
})
```

### Playwright Fixture（推荐用法）

```typescript
// 零配置
import { test, expect } from 'playwright-unified-logger/fixtures'

// 自定义配置
import { createLoggerFixture } from 'playwright-unified-logger/fixtures'
const test = createLoggerFixture({ logLevel: 'verbose' })

test('my test', async ({ page, unifiedLogger }) => {
  // unifiedLogger 自动创建和销毁
})
```

### 子日志器（可单独使用）

```typescript
import { NetworkLogger, ConsoleLogger, RouteLogger, TestCodeLogger } from 'playwright-unified-logger'
```

### 事件总线

```typescript
logger.events.on('network:error', (event) => {
  // 自定义处理
})
```

### 配置接口

```typescript
interface UnifiedLoggerConfig {
  logLevel?: 'mini' | 'normal' | 'verbose' | 'silent'
  compactMode?: boolean
  outputDir?: string
  deduplication?: boolean
  aggregation?: boolean
  network?: NetworkLoggerOptions
  console?: ConsoleLoggerOptions
  route?: RouteLoggerOptions
  testCode?: TestCodeLoggerOptions
}
```

### 环境变量

| 变量 | 值 | 默认 |
|---|---|---|
| `UNIFIED_LOG_LEVEL` | mini / normal / verbose / silent | mini |
| `UNIFIED_LOG_DEDUP` | true / false | true |
| `UNIFIED_LOG_AGGREGATE` | true / false | true |
| `UNIFIED_LOG_COMPACT` | true / false | false |
| `UNIFIED_LOG_OUTPUT_DIR` | 目录路径 | test-results/unified-logs |
| `DEMO_LOG_*` | 旧版兼容（同上） | — |

---

## 与旧版的主要变更

| 旧版 | 新版 | 说明 |
|---|---|---|
| `logger.console` | `logger.browserConsole` | 避免与全局 console 冲突，旧名保留为 deprecated |
| URL 匹配请求 | `WeakMap<Request, ...>` | 修复并发请求错配 bug |
| 逐次 fs.appendFile | `WriteBuffer` 缓冲写入 | 性能优化 |
| 硬编码过滤模式 | 可配置 `filterPatterns` | |
| 硬编码 API 路径 | 可配置 `urlFilter` | |
| 硬编码重定向检测 | 可配置 `redirectDetector` | |
| 仅环境变量配置 | 编程配置 + 环境变量 | 优先级：构造函数 > config 对象 > 环境变量 |
| 无事件机制 | `LoggerEventBus` | 可订阅日志事件 |
| 无 Fixture 导出 | `fixtures.ts` | 零配置即可使用 |
