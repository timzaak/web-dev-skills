# Frontend 常用模式

本页只记录当前项目已经采用、且值得重复复用的前端实现模式。

使用规则：
- 这里写“本项目怎么做”，不写长篇库教程
- 如与仓库真实实现冲突，以 `frontend/src/` 当前事实为准
- 更底层的架构事实看 `./development.md`

## 1. Query

- 服务端状态优先使用 TanStack Query
- 复用稳定的 `queryKey` 组织方式，不临时发明同义 key
- 可复用查询优先抽成 `queryOptions`
- mutation 完成后优先 `invalidateQueries`，只有明确需要时才做 optimistic update

```ts
import { queryOptions } from '@tanstack/react-query'
import { listUsers } from '@/lib/api-generated'
import { handleApiResponse } from '@/lib/api-utils'

export function userListOptions() {
  return queryOptions({
    queryKey: ['users', 'list'],
    queryFn: async () => handleApiResponse(await listUsers()),
  })
}
```

## 2. Router

- 路由真相以 `frontend/src/routes/` 和 `frontend/src/routeTree.gen.ts` 为准
- 当前默认使用固定单租户路径
- 列表页搜索参数优先使用 `validateSearch`
- 参数访问和跳转保持类型安全，优先复用当前路由文件已有模式

```ts
import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'

export const Route = createFileRoute('/manage/users')({
  validateSearch: z.object({
    page: z.number().default(1).catch(1),
    search: z.string().default(''),
  }),
})
```

## 3. Form

- 表单优先使用 `useAppForm`
- 验证规则用 Zod schema
- 错误展示复用 `getFieldErrorMessage`
- 提交逻辑优先复用现有 `useFormMutation` / 共享表单容器模式

```tsx
import { useAppForm } from '@/components/ui/tanstack-form'

const form = useAppForm({
  schema: createSchema,
  defaultValues: { name: '' },
  onSubmit: async ({ value }) => {
    await mutate(value)
  },
})
```

## 4. API

- API 调用优先复用 `frontend/src/lib/api-generated/`
- 响应处理优先走 `handleApiResponse`
- OpenAPI 契约变化后先刷新生成物，再继续改页面逻辑

```ts
import { createClientApp } from '@/lib/api-generated'
import { handleApiResponse } from '@/lib/api-utils'

await handleApiResponse(
  await createClientApp({ body: payload }),
)
```

## 5. Tailwind

- 样式优先复用共享 UI 组件和现有 utility 组合
- 项目级 token / theme 约定优先沿用现有实现，不平行新增一套设计语言
- Tailwind v4 相关主题定制优先放在项目统一样式入口，而不是散落到单页私有规则里

```tsx
<div className="flex items-center gap-2 rounded-md border px-3 py-2">
  <span className="text-sm font-medium">Label</span>
</div>
```
