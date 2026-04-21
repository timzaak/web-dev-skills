# 前端文件模板

本文件包含前端所有需要生成的文件内容模板。
占位符：`{{PROJECT_NAME}}` (kebab-case), `{{PROJECT_NAME_PASCAL}}` (PascalCase)

---

## 1. frontend/package.json

```json
{
  "name": "{{PROJECT_NAME}}",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --port 3000",
    "build": "vite build && tsc --noEmit",
    "preview": "vite preview",
    "type-check": "tsc --noEmit",
    "generate-api": "cargo run --manifest-path ../backend/app/Cargo.toml -- --export-openapi ../frontend/api.json && openapi-ts",
    "predev": "npm run generate-api",
    "prebuild": "npm run generate-api"
  },
  "dependencies": {
    "@radix-ui/react-label": "^2.1.1",
    "@radix-ui/react-slot": "^1.2.4",
    "@tanstack/react-form": "^1.27.6",
    "@tanstack/react-query": "^5.90.16",
    "@tanstack/react-query-devtools": "^5.91.3",
    "@tanstack/react-router": "^1.163.3",
    "@tanstack/react-router-devtools": "^1.163.3",
    "@tanstack/router-plugin": "^1.163.3",
    "@tailwindcss/vite": "^4.2.1",
    "axios": "^1.13.4",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "lucide-react": "^0.562.0",
    "react": "^19.2.4",
    "react-dom": "^19.2.4",
    "sonner": "^2.0.7",
    "tailwind-merge": "^3.5.0",
    "tailwindcss": "^4.2.1",
    "tw-animate-css": "^1.4.0",
    "zod": "^4.3.6",
    "zustand": "^5.0.11"
  },
  "devDependencies": {
    "@hey-api/openapi-ts": "^0.92.3",
    "@types/node": "^25.0.3",
    "@types/react": "^19.2.7",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^5.1.2",
    "typescript": "^5.9.3",
    "vite": "^7.3.1"
  }
}
```

> **Scripts 说明**：
> - `dev` — 启动开发服务器（端口 3000），自动先执行 generate-api
> - `build` — 构建生产版本，包含类型检查
> - `generate-api` — 从后端 OpenAPI 规范生成 TypeScript API 客户端
> - `predev` / `prebuild` — npm 生命周期钩子，在 dev/build 前自动生成 API

---

## 2. frontend/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
```

> **注意**：运行 `npm run generate-api` 后，`src/lib/api-generated/` 目录会被自动创建。
> 如需将其纳入类型检查，将 include 改为 `["src", "src/lib/api-generated"]`。

---

## 3. frontend/vite.config.ts

```typescript
/**
 * Vite 配置文件
 *
 * 这个文件配置了前端的构建工具和开发服务器。
 * 主要配置项说明：
 *
 * 1. plugins — Vite 插件列表
 *    - tailwindcss()：集成 Tailwind CSS v4，自动处理 CSS
 *    - tanstackRouter()：TanStack Router 的 Vite 插件，
 *      基于文件系统自动生成路由（src/routes/ 目录下的文件）
 *    - react()：支持 JSX 和 React Fast Refresh
 *
 * 2. resolve.alias — 路径别名
 *    - @ → ./src，可以在代码中用 @/components/ui 代替相对路径
 *
 * 3. server.proxy — 开发服务器代理
 *    - /api → 后端服务器（默认 localhost:8080）
 *    这样前端请求 /api/xxx 会自动转发到后端，避免跨域问题
 *
 * 修改指南：
 * - 后端端口变化 → 修改 proxy.target
 * - 添加新插件 → 在 plugins 数组中添加
 * - 修改端口 → 修改 package.json 中 dev 脚本的 --port 参数
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [
    tailwindcss(),
    tanstackRouter({
      target: 'react',
      autoCodeSplitting: true,
    }),
    react(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  optimizeDeps: {
    include: ['@tanstack/react-query', '@tanstack/react-router'],
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        withCredentials: true,
      },
    },
  },
})
```

---

## 4. frontend/openapi-ts.config.ts

```typescript
/**
 * OpenAPI TypeScript 客户端生成配置
 *
 * 这个文件配置 @hey-api/openapi-ts 工具，它会：
 * 1. 读取后端导出的 OpenAPI 规范（api.json）
 * 2. 生成类型安全的 TypeScript API 客户端代码
 * 3. 输出到 src/lib/api-generated/ 目录
 *
 * 使用方式：
 * - npm run generate-api — 手动触发生成
 * - npm run dev / npm run build — 自动在构建前生成
 *
 * 修改指南：
 * - 后端新增接口后，重新运行 generate-api 即可自动更新客户端
 * - 需要自定义请求处理 → 修改 services 配置
 * - 使用其他 HTTP 客户端 → 修改 client 字段（如改为 'fetch'）
 */
import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  input: './api.json',
  output: {
    path: './src/lib/api-generated',
  },
  services: {
    asClass: false,
    name: '{{name}}',
    include: 'responses|requests|all',
    operationId: true,
    response: 'body',
  },
  client: 'axios',
})
```

---

## 5. frontend/index.html

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{PROJECT_NAME_PASCAL}}</title>
  </head>
  <body>
    <!-- React 应用的挂载点 -->
    <!-- main.tsx 中的 ReactDOM.createRoot 会将 React 组件渲染到这里 -->
    <div id="app"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

---

## 6. frontend/src/main.tsx

```typescript
/**
 * 应用入口文件
 *
 * 这是整个前端应用的起点。它做了以下事情：
 *
 * 1. 引入全局样式（styles.css，包含 Tailwind CSS）
 * 2. 创建 React Query 客户端（用于数据请求和缓存管理）
 * 3. 创建 TanStack Router 路由实例（基于文件路由）
 * 4. 将路由和 Query 客户端挂载到 DOM
 *
 * 工作流程：
 * index.html → 加载此文件 → 创建 Router → 渲染到 #app 元素
 *
 * 扩展指南：
 * - 修改全局配置（如 staleTime）→ 修改 queryClient 的 defaultOptions
 * - 添加全局 Provider（如主题、国际化）→ 在 StrictMode 内添加
 * - 修改路由行为 → 编辑 src/routes/__root.tsx
 */
import './styles.css'
import { StrictMode } from 'react'
import { createRouter } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from '@tanstack/react-router'
import ReactDOM from 'react-dom/client'
import { routeTree } from './routeTree.gen'

// React Query 客户端配置
// staleTime: 数据被认为是"新鲜"的时间（5分钟内不会重新请求）
// retry: 请求失败不自动重试（可根据需要调整）
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: false,
    },
  },
})

// 创建路由器实例
// routeTree 是由 TanStack Router 插件根据 src/routes/ 目录自动生成的
// 每个文件对应一个路由，文件路径决定 URL 路径
export const router = createRouter({
  routeTree,
  context: {
    queryClient,
  },
})

// TypeScript 类型声明 — 让路由器知道可用的路由类型
// 这提供了完整的类型安全和自动补全
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
  interface RouterContext {
    queryClient: QueryClient
  }
}

declare global {
  interface Window {
    router: typeof router
  }
}

// 开发模式下将路由实例暴露到 window，方便调试
if (import.meta.env.DEV) {
  window.router = router
}

// 渲染应用
// StrictMode 会在开发模式下触发额外的渲染来检测副作用
const rootElement = document.getElementById('app')!

ReactDOM.createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>
)
```

---

## 7. frontend/src/styles.css

```css
/**
 * 全局样式文件
 *
 * 这个文件使用了 Tailwind CSS v4 的新语法。
 * 主要功能：
 *
 * 1. @import 'tailwindcss' — 引入 Tailwind CSS 核心
 * 2. @import 'tw-animate-css' — 引入动画库
 * 3. @theme inline — 定义设计令牌（颜色、圆角等 CSS 变量）
 * 4. :root / .dark — 定义亮色和暗色主题的颜色变量
 *
 * 自定义指南：
 * - 添加全局颜色 → 在 :root 和 .dark 中添加 CSS 变量
 * - 修改圆角 → 调整 --radius 值
 * - 添加自定义动画 → 在文件末尾添加 @keyframes
 */
@import 'tailwindcss';
@import 'tw-animate-css';

@custom-variant dark (&:is(.dark *));

@layer base {
  *,
  ::after,
  ::before,
  ::backdrop,
  ::file-selector-button {
    border-color: var(--color-gray-200, currentcolor);
  }
}

html {
  color-scheme: light dark;
}

* {
  @apply border-gray-200 dark:border-gray-800;
}

body {
  @apply bg-gray-50 text-gray-950 dark:bg-gray-900 dark:text-gray-200;
}

@theme inline {
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
  --radius-2xl: calc(var(--radius) + 8px);
  --radius-3xl: calc(var(--radius) + 12px);
  --radius-4xl: calc(var(--radius) + 16px);
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --color-sidebar: var(--sidebar);
  --color-sidebar-foreground: var(--sidebar-foreground);
  --color-sidebar-primary: var(--sidebar-primary);
  --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
  --color-sidebar-accent: var(--sidebar-accent);
  --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
  --color-sidebar-border: var(--sidebar-border);
  --color-sidebar-ring: var(--sidebar-ring);
}

:root {
  --radius: 0.625rem;
  --background: oklch(1 0 0);
  --foreground: oklch(0.141 0.005 285.823);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.141 0.005 285.823);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.141 0.005 285.823);
  --primary: oklch(0.21 0.006 285.885);
  --primary-foreground: oklch(0.985 0 0);
  --secondary: oklch(0.967 0.001 286.375);
  --secondary-foreground: oklch(0.21 0.006 285.885);
  --muted: oklch(0.967 0.001 286.375);
  --muted-foreground: oklch(0.552 0.016 285.938);
  --accent: oklch(0.967 0.001 286.375);
  --accent-foreground: oklch(0.21 0.006 285.885);
  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.92 0.004 286.32);
  --input: oklch(0.92 0.004 286.32);
  --ring: oklch(0.705 0.015 286.067);
  --chart-1: oklch(0.646 0.222 41.116);
  --chart-2: oklch(0.6 0.118 184.704);
  --chart-3: oklch(0.398 0.07 227.392);
  --chart-4: oklch(0.828 0.189 84.429);
  --chart-5: oklch(0.769 0.188 70.08);
  --sidebar: oklch(0.985 0 0);
  --sidebar-foreground: oklch(0.141 0.005 285.823);
  --sidebar-primary: oklch(0.21 0.006 285.885);
  --sidebar-primary-foreground: oklch(0.985 0 0);
  --sidebar-accent: oklch(0.967 0.001 286.375);
  --sidebar-accent-foreground: oklch(0.21 0.006 285.885);
  --sidebar-border: oklch(0.92 0.004 286.32);
  --sidebar-ring: oklch(0.705 0.015 286.067);
}

.dark {
  --background: oklch(0.141 0.005 285.823);
  --foreground: oklch(0.985 0 0);
  --card: oklch(0.21 0.006 285.885);
  --card-foreground: oklch(0.985 0 0);
  --popover: oklch(0.21 0.006 285.885);
  --popover-foreground: oklch(0.985 0 0);
  --primary: oklch(0.92 0.004 286.32);
  --primary-foreground: oklch(0.21 0.006 285.885);
  --secondary: oklch(0.274 0.006 286.033);
  --secondary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.274 0.006 286.033);
  --muted-foreground: oklch(0.705 0.015 286.067);
  --accent: oklch(0.274 0.006 286.033);
  --accent-foreground: oklch(0.985 0 0);
  --destructive: oklch(0.704 0.191 22.216);
  --border: oklch(1 0 0 / 10%);
  --input: oklch(1 0 0 / 15%);
  --ring: oklch(0.552 0.016 285.938);
  --chart-1: oklch(0.488 0.243 264.376);
  --chart-2: oklch(0.696 0.17 162.48);
  --chart-3: oklch(0.769 0.188 70.08);
  --chart-4: oklch(0.627 0.265 303.9);
  --chart-5: oklch(0.645 0.246 16.439);
  --sidebar: oklch(0.21 0.006 285.885);
  --sidebar-foreground: oklch(0.985 0 0);
  --sidebar-primary: oklch(0.488 0.243 264.376);
  --sidebar-primary-foreground: oklch(0.985 0 0);
  --sidebar-accent: oklch(0.274 0.006 286.033);
  --sidebar-accent-foreground: oklch(0.985 0 0);
  --sidebar-border: oklch(1 0 0 / 10%);
  --sidebar-ring: oklch(0.552 0.016 285.938);
}

@layer base {
  * {
    @apply border-border outline-ring/50;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

---

## 8. frontend/src/routes/__root.tsx

```typescript
/**
 * 根路由文件
 *
 * TanStack Router 使用文件系统路由：
 * - src/routes/__root.tsx → 所有路由的父级布局
 * - src/routes/index.tsx → 首页 (/)
 * - src/routes/about.tsx → /about
 * - src/routes/auth/login.tsx → /auth/login
 * - src/routes/manage/dashboard.tsx → /manage/dashboard
 *
 * 文件名以 __ 开头的表示布局路由（不会产生 URL 段）
 * Outlet 组件是子路由渲染的位置
 *
 * 这个文件定义了：
 * 1. 全局布局（Toast 通知容器）
 * 2. 开发工具（React Query DevTools、Router DevTools）
 *
 * 扩展指南：
 * - 添加全局导航栏 → 在 Outlet 上方添加 <nav> 组件
 * - 添加全局侧边栏 → 在 Outlet 旁添加 sidebar 组件
 * - 添加认证守卫 → 在 beforeLoad 或 loader 中检查认证状态
 */
import { createRootRouteWithContext, Outlet } from '@tanstack/react-router'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from '@/components/ui/sonner'
import type { QueryClient } from '@tanstack/react-query'

// 路由上下文类型 — 所有路由都能访问这些数据
type RouterContext = {
  queryClient: QueryClient
}

// 创建根路由
// createRootRouteWithContext 允许子路由通过 context 访问 QueryClient
export const Route = createRootRouteWithContext<RouterContext>()({
  // beforeLoad — 在路由加载前执行（适合做认证检查）
  // loader — 在组件渲染前加载数据
  component: RootComponent,
})

function RootComponent() {
  return (
    <>
      {/* 子路由渲染位置 — 所有页面内容在这里显示 */}
      <Outlet />

      {/* 全局 Toast 通知容器 — 使用 sonner 库 */}
      {/* 在任何组件中调用 toast('消息') 即可显示通知 */}
      <Toaster />

      {/* 开发工具 — 仅在开发模式显示 */}
      {import.meta.env.DEV && (
        <>
          <ReactQueryDevtools />
        </>
      )}
    </>
  )
}
```

---

## 9. frontend/src/routes/index.tsx

```typescript
/**
 * 首页路由
 *
 * 文件路径 src/routes/index.tsx → URL: /
 * 这是用户访问根路径时看到的页面。
 *
 * 修改指南：
 * - 修改首页内容 → 编辑下方 HomeRoute 组件
 * - 添加子路由 → 在 src/routes/ 下创建新文件
 */
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomeRoute,
})

function HomeRoute() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">
          Welcome to {{PROJECT_NAME_PASCAL}}
        </h1>
        <p className="text-muted-foreground">
          Project initialized. Start building!
        </p>
      </div>
    </div>
  )
}
```

---

## 10. frontend/src/lib/api-client.ts

```typescript
/**
 * API 客户端配置
 *
 * 这个文件配置了 Axios 实例，用于所有 HTTP 请求。
 *
 * 工作原理：
 * 1. 创建一个 Axios 实例，设置了基础 URL
 * 2. 添加请求拦截器（可用于添加认证 Token）
 * 3. 添加响应拦截器（可用于统一错误处理）
 *
 * 与自动生成的 API 客户端的关系：
 * - openapi-ts 根据 api.json 生成类型安全的 API 函数
 * - 生成的代码使用此处的 Axios 实例发送请求
 * - 生成的代码在 src/lib/api-generated/ 目录下
 *
 * 修改指南：
 * - 修改 API 基础路径 → 修改 baseURL
 * - 添加认证 Token → 在请求拦截器中添加 headers
 * - 统一错误处理 → 在响应拦截器中处理 error
 */
import axios from 'axios'

const apiClient = axios.create({
  // 开发环境通过 Vite proxy 转发到后端
  // 生产环境需要配置实际的 API 地址
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 — 在每个请求发送前执行
apiClient.interceptors.request.use(
  (config) => {
    // 在这里可以添加认证 Token
    // const token = getAuthToken()
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 — 在每个响应返回后执行
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // 统一处理 401 未认证错误
    if (error.response?.status === 401) {
      // 跳转到登录页面
      window.location.href = '/auth/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

---

## 11. frontend/src/components/ui/sonner.tsx

```typescript
/**
 * Toast 通知组件
 *
 * 基于 sonner 库的 Toast 通知组件。
 * 使用方式：
 *
 * import { toast } from 'sonner'
 * toast.success('操作成功')
 * toast.error('操作失败')
 * toast('普通消息')
 *
 * 这个组件只是重新导出 sonner，方便统一管理和自定义主题。
 * 如果需要自定义 Toast 样式，修改此文件即可。
 */
export { Toaster, toast } from 'sonner'
```

---

## 12. frontend/src/routeTree.d.ts

```typescript
/* eslint-disable @typescript-eslint/no-empty-object-type */

/**
 * 路由树类型声明
 *
 * 这个文件为 TanStack Router 插件自动生成的 routeTree.gen.ts 提供类型声明。
 * 首次运行 npm run dev 后，插件会生成实际的 routeTree.gen.ts 文件，
 * 之后此声明文件会被自动替代。
 *
 * 如果类型报错，运行 npm run dev 让插件重新生成路由文件。
 */
declare module './routeTree.gen' {
  import type { AnyRoute } from '@tanstack/react-router'

  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface RouteTree extends AnyRoute {}
  const routeTree: RouteTree
  export { routeTree }
}
```

---

## 生成时的注意事项

1. 所有 `{{PROJECT_NAME}}` 替换为实际项目名（kebab-case）
2. 所有 `{{PROJECT_NAME_PASCAL}}` 替换为 PascalCase
3. 前端文件的注释必须保留 — 这些注释帮助开发者理解项目结构
4. 依赖版本应根据 Context7 查询结果更新
5. TanStack Router 版本更新可能影响路由 API，需确认兼容性
6. 如果不需要暗色主题，可以简化 styles.css 中的 .dark 块
