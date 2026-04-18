# 前端测试指南

> **Vitest + @testing-library/react + MSW**
> **运行模式**: JSDOM
> **无需后端环境**: 是
> **测试策略**: Demo 承担完整故事与页面主链路，Vitest 只覆盖高价值逻辑和 Demo 难稳定覆盖的边界

## 测试环境配置

```bash
# 开发模式（监听文件变化）
npm run test

# 单次运行
npm run test:run

# 运行特定文件
npm run test:run -- src/components/auth/__tests__/password-strength-meter.test.tsx

# 查看测试覆盖率
npm run test:coverage

# 交互式 UI
npm run test:ui
```

## 测试边界

### 何时编写 Vitest

仅在以下场景编写 Vitest：
- Hook、纯函数、数据转换、schema、权限判断、缓存 key 等纯逻辑
- 组件内部状态机、派生状态、条件分支
- Demo 难以稳定覆盖的异常边界和特殊错误场景
- 需要快速反馈的局部回归

### 不应规划为 Vitest 的场景

以下场景默认交给 Demo 或其他专项工具，不应在 `/t-task` 中规划为前端 Vitest：
- 页面级 happy-path
- 完整用户故事或跨组件业务流程
- 常规表单提交流程与正常交互链路
- 页面级集成测试
- 可访问性合规验证
- 性能预算验证
- 视觉回归验证

### 与 Demo-first 的关系

- 测试层级选择以 [环境与测试总览](/guides/core/environment-and-testing-guide.md) 为准。
- 已由 Demo 覆盖的完整流程，不再重复补同路径 Vitest。
- 如改动只影响页面主链路且 Demo 已覆盖，可在任务中明确写“不新增 Vitest，由 Demo 覆盖”。

## 当前仓库测试基线

### Vitest 配置事实

当前仓库前端测试基线以 `frontend/vitest.config.ts` 和 `frontend/src/test/setup.ts` 为准：
- 环境为 `jsdom`
- 启用 `globals: true`
- `testTimeout` 为 5000ms
- `setupFiles` 指向 `src/test/setup.ts`
- 测试间隔离开启，MSW 在全局 setup 中启动

### 全局 setup 行为

MSW 和全局 mock 在 `src/test/setup.ts` 中统一处理：

```ts
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' })
})

afterEach(() => {
  server.resetHandlers()
})

beforeEach(() => {
  vi.clearAllMocks()
})

afterAll(() => {
  server.close()
})
```

说明：
- 未匹配的请求会告警，不会静默吞掉
- 每个测试结束后重置 MSW handlers
- 每个测试开始前清空 `vi` mocks，保持隔离

### 测试目录分布

当前仓库的 Vitest 用例分布主要在：
- `frontend/src/lib/__tests__/`
- `frontend/src/components/**/__tests__/`
- `frontend/src/test/__tests__/`

`frontend/src/test/` 同时承载 setup 和 mocks。`frontend/tests/` 不是当前主测试目录事实。

## MSW 使用规则

### Mock Handlers 位置

- 全局 handlers 定义在 `frontend/src/test/mocks/handlers.ts`
- server 定义在 `frontend/src/test/mocks/server.ts`
- 测试内临时覆盖使用 `server.use(...)`

### 推荐写法

```tsx
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mocks/server'

test('shows error message when API returns 401', async () => {
  server.use(
    http.post('/api/auth/login', () =>
      HttpResponse.json({ message: 'Invalid credentials' }, { status: 401 })
    )
  )

  render(<LoginForm />)

  await userEvent.click(screen.getByTestId('submit-button'))

  expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument()
})
```

说明：
- 优先 Mock 边界，不直接请求真实 API
- 每个测试只覆盖自己关心的 handler
- 异步结果使用 `await screen.findBy*` 或 `waitFor`

## API 与查询规范

### 交互 API

统一使用 Testing Library + `userEvent`：
- 使用 `render(<Component />)`，不需要 `await`
- 使用 `await userEvent.click(...)`、`await userEvent.type(...)`
- 不直接改 DOM value 再手动派发事件

```tsx
render(<MyComponent />)
await userEvent.type(screen.getByTestId('email-input'), 'user@example.com')
await userEvent.click(screen.getByRole('button', { name: /submit/i }))
```

### 查询优先级

1. `getByRole`
2. `getByLabelText`
3. `getByText`
4. `getByTestId`
5. `queryBy*`
6. `container.querySelector` 仅在访问 DOM 属性或复杂选择器时使用

实现层要求：
- P0/P1/P2 元素必须添加 `data-testid`
- 规则见 [data-testid 编写规范](/guides/frontend/testid-standards.md)

### 异步断言

正确写法：

```tsx
await screen.findByTestId('loading')
await waitFor(() => {
  expect(mockOnSave).toHaveBeenCalled()
})
```

不要写成：

```tsx
expect(screen.findByTestId('loading')).toBeDefined()
```

## 推荐测试模式

### 逻辑型组件测试

```tsx
test('shows validation error when derived state becomes invalid', async () => {
  render(<RegistrationConfigForm {...props} />)

  await userEvent.click(screen.getByTestId('reg-save-button'))

  expect(await screen.findByText(/required/i)).toBeInTheDocument()
})
```

### 条件渲染测试

```tsx
test('renders alert when message is provided', () => {
  render(<Alert type="error" message="Error!" />)
  expect(screen.getByTestId('alert-error')).toBeInTheDocument()
})

test('does not render when message is empty', () => {
  render(<Alert type="error" message="" />)
  expect(screen.queryByTestId('alert-error')).toBeNull()
})
```

### Mock 模块或 hooks

```tsx
vi.mock('@/hooks/use-form-mutation', () => ({
  useFormMutation: vi.fn(),
}))

test('submits through wrapped mutation hook', async () => {
  vi.mocked(useFormMutation).mockReturnValue({
    isSubmitting: false,
    mutate: mockMutate,
  } as never)

  render(<MyForm />)
  await userEvent.click(screen.getByTestId('submit-button'))

  expect(mockMutate).toHaveBeenCalled()
})
```

### React Query 场景

需要 QueryClient 时，在测试内部显式创建最小 wrapper，不把一次性 wrapper 误写成全局规范：

```tsx
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
}
```

说明：
- 当前 `frontend/src/test/test-utils.tsx` 不是稳定的仓库级标准入口
- 新测试优先在文件内按需声明 wrapper，只有形成稳定复用后再统一收敛

## 断言与调试

常见断言：

```tsx
expect(screen.getByTestId('form')).toBeInTheDocument()
expect(screen.queryByTestId('error')).toBeNull()
expect(screen.getByText('Success')).toBeVisible()
expect(screen.getByRole('button')).toBeDisabled()
```

调试方式：

```tsx
const { container } = render(<MyComponent />)
console.log(container.innerHTML)
```

注意：
- `setTimeout` 只用于临时调试，不作为正式等待方式
- 正式测试统一使用 `findBy*` 或 `waitFor`

## 最佳实践

### DO

1. 测试用户可观察行为，而不是第三方库实现细节。
2. 用最小 mock 覆盖当前场景，避免过度伪造整条业务链路。
3. 对业务状态、权限、错误提示、禁用态做断言。
4. 保留业务驱动的类名断言，避免纯视觉样式断言。

### DON'T

1. 不要请求真实后端 API。
2. 不要把页面完整 happy-path 再复制成 Vitest。
3. 不要依赖脆弱选择器、纯样式类名或 DOM 层级。
4. 不要使用硬编码等待代替异步查询。
5. 不要把历史仓库或旧模板的测试工具包装器当成当前标准。

## 测试类型说明

| 测试类型 | 目的 |
|----------|------|
| **Vitest 单元测试** | Hook、纯函数、数据转换、schema、权限判断、组件内部状态机、异常边界 |
| **Vitest 集成测试（少量）** | Demo 难覆盖的复杂局部状态逻辑、特殊错误场景 |
| **Demo 测试** | 完整用户故事、跨模块流程、页面 happy-path、表单完整流程、产品展示 |

## 规划约束

- `frontend/test.md` 默认只列高价值逻辑型 Vitest 任务
- 若需求已由 Demo 覆盖，应优先记录“不新增 Vitest，由 Demo 覆盖”
- 不要为了“补测试”而增加页面级、性能、可访问性或视觉回归 Vitest

## 参考

- [data-testid 编写规范](/guides/frontend/testid-standards.md)
- [环境与测试总览](/guides/core/environment-and-testing-guide.md)
- [质量门禁](/guides/core/quality.md)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [MSW (Mock Service Worker)](https://mswjs.io/)
