# 前端开发、UI 决策与常用模式规范

Frontend 主规范，定义插件级稳定约束、UI 决策默认依据与高频实现模式；目标项目的真实路由、目录职责、组件体系、token 约定和依赖版本始终优先于本页默认值。

相关入口：
- 测试规则：`${CLAUDE_PLUGIN_ROOT}/guides/frontend/testing.md`
- 完成前验证与验收：`${CLAUDE_PLUGIN_ROOT}/guides/frontend/quality.md`
- `data-testid` 规则：`${CLAUDE_PLUGIN_ROOT}/guides/frontend/testid-standards.md`

## 1. 技术基线、目录与路由事实

先读取目标项目的 `frontend/package.json`、路由入口、API 客户端生成配置和现有页面代码，确认真实技术栈与命令。默认模板倾向 React + TypeScript + Vite + TanStack Router / Query / Form + Zustand + Zod + Tailwind CSS + Radix UI + Vitest / Testing Library / MSW + `@hey-api/openapi-ts`，但不得覆盖目标项目事实。

- **目录与生成物**：以 `frontend/src/` 当前实现为准；生成代码目录视为派生物，不手工维护业务逻辑。
- **路由事实**：以当前路由文件、路由生成物和路由配置为准，新页面遵循现有文件路由结构和分组方式，不沿用历史模板路由。
- **数据与状态分工**：服务端数据（查询、缓存、失效、重新获取）由 TanStack Query 独占管理，不进入 Zustand；Zustand 只承载全局客户端/UI 状态（开关、草稿、跨页面交互状态，跨组件记住某条服务端数据选中态时仅存 ID 引用）。组件通过 selector 订阅最小所需状态，订阅对象/数组时做浅比较。
- **API 契约同步**：API 契约变化后先刷新 OpenAPI 生成物，再写页面逻辑。
- **范围边界**：某个 feature 的特殊表单、OAuth 或局部技巧写在该 feature 设计/实现附近，不回写成全局主规范。

## 2. UI 决策规范（设计阶段与实现默认依据）

目标项目的组件体系和设计语言优先；无明确约定时遵循以下规则：

### 复用阶梯与组件选型

新建任何组件或依赖前按序判断：**Inspect → Reuse → Adapt → Extend → Create**（新建必须说明前四级不可行的理由；现有依赖或原生能力能覆盖时不引入新依赖；局部调整保持最小 diff）。

| 场景 | 默认选择 |
| --- | --- |
| 选项 4–10 个 | 原生 `<select>` |
| 选项超过 10 个或需要搜索 | combobox |
| 列表少于 100 条 | 普通列表，不虚拟化 |
| 平级视图切换 | tabs / segmented |
| 展示型内容折叠 | accordion |
| 异步时长不确定 | 骨架屏，超过 300ms 才显示 |
| 已知短操作 | 按钮内 loading |
| 可点击、可触发 | 语义元素（`<button>` / `<a>`），禁止 `<div onClick>` |

### 交互状态、无障碍底线与视觉纪律

- **状态与反馈**：可交互组件覆盖 hover / focus / active / disabled / loading；数据视图覆盖加载 / 空态（可行动）/ 错误（提供恢复路径）/ 权限受限；反馈时机 100ms 即时反馈、300ms 加载指示、超 3s 说明进度或提供取消。
- **无障碍底线（不可省略）**：全键盘可操作（Tab / Enter / Space）；图标按钮有可访问名（`aria-label` 或可见文本）；表单控件与 `label` 关联（`placeholder` 不充当 label）；颜色不是唯一信息载体；触控目标不小于 44px。
- **视觉与复杂度准入**：大面积灰阶克制用色，强调色留给最重要动作；尺寸与 z-index 来自项目现有 token/档位；"高级"靠排版、间距和层级而非堆砌装饰，"简洁"不是删说明文案或全收进汉堡菜单。装饰性效果（glass、glow、particles、3D 等）须通过三问（是否服务当前任务 / 是否降低其他复杂度 / 删掉是否损害可用性、无障碍或信息层级），全"否"即删。

## 3. 项目常用实现模式

如与仓库真实实现冲突，以 `frontend/src/` 当前事实为准：

- **Query**：复用稳定 `queryKey`，可复用查询抽成 `queryOptions`，mutation 后优先 `invalidateQueries`（确有必要才做 optimistic update）。

```ts
export function userListOptions() {
  return queryOptions({
    queryKey: ['users', 'list'],
    queryFn: async () => handleApiResponse(await listUsers()),
  })
}
```

- **Router**：列表页搜索参数优先使用 `validateSearch` + Zod：

```ts
export const Route = createFileRoute('/example')({
  validateSearch: z.object({
    page: z.number().default(1).catch(1),
    search: z.string().default(''),
  }),
})
```

- **Form**：优先 `useAppForm` + Zod schema + `getFieldErrorMessage` + `onSubmit` 回调（复用项目现有 `useFormMutation` / 表单容器）：

```tsx
const form = useAppForm({
  schema: createSchema,
  defaultValues: { name: '' },
  onSubmit: async ({ value }) => {
    await mutate(value)
  },
})
```

- **API 与 Tailwind**：API 调用复用生成目录与 `handleApiResponse`；Tailwind 优先复用共享组件与现有 utility，主题定制放在项目统一样式入口。

## 4. 完成前最低验证

```bash
cd frontend && npm run type-check && npm run build
```

完整门禁、常见类型错误排查及验收标准见 `${CLAUDE_PLUGIN_ROOT}/guides/frontend/quality.md`。
