# Demo 选择器与 Page Object 编写规范

**定位**：本文件是 Demo/E2E 选择器策略与 Page Object Model (POM) 的唯一主规范。
**适用对象**：web-demo-dev、frontend-dev、测试维护人员。

## 1. 复杂度决策（MANDATORY）

| 复杂度 | 参考规模 | 推荐方案 |
|---|---|---|
| 简单 | < 50 行 | 可直接写测试 |
| 中等 | 50-200 行 | 使用 `selectors.ts` 集中管理 |
| 复杂 | > 200 行或跨页面流程 | MANDATORY：使用 POM |

触发 POM 的典型信号：选择器在多个测试重复出现、同一页面操作在多个场景复用、单文件维护成本明显升高。

## 2. 选择器策略（MANDATORY）

### 选择器优先级

| 优先级 | 类型 | 使用条件 | 备注 |
|---|---|---|---|
| 1 | `getByRole` | 有明确语义角色与可访问名称 | 首选 |
| 2 | `getByLabel` / `getByPlaceholder` | 表单可见属性可稳定定位 | 表单优先 |
| 3 | `getByTestId` | 复杂组件、语义不足、文案不稳定 | 稳定后备 |
| 4 | `getByText` | 临时或低风险场景 | 注意国际化与歧义 |
| 5 | `locator(css/xpath)` | 上述都不可用时 | 限制作用域并在代码旁说明原因 |

AVOID：依赖样式类名（如 `.btn-primary`）、深层 DOM 路径（如 `div > div:nth-child(2)`）、全局无约束文本匹配，以及将 `sonner`、toast、Snackbar 等自动消失提示作为主判断条件或唯一验收依据。

### 与 `data-testid` 协同及回退链

- `data-testid` 不是默认第一选择，但必须为关键交互准备稳定后备；第三方组件语义不完整、自定义复杂组件或文案频繁变化/多语言场景推荐直接使用 `getByTestId`。
- 建议在 `demo/e2e/selectors.ts` 管理共享选择器：主选择器必须是当前最稳定方案，后备选择器最多 1-2 个，禁止堆叠过多回退链掩盖真实问题。

```ts
export const SELECTORS = {
  buttons: {
    addUser: [
      'role=button[name="Add User"]',
      '[data-testid="user-add-button"]',
    ],
  },
}
```

## 3. Page Object Model (POM) 规范

### 文件结构与职责划分

```text
demo/e2e/
├── pages/
│   ├── base-page.ts
│   ├── <entity>-page.ts
│   └── ...
├── selectors.ts
└── <role>/*.e2e.ts
```

- `BasePage`：通用能力（导航、通用等待、通用断言）。
- `XxxPage`（文件 `xxx-page.ts`）：页面级业务操作与页面级断言；元素定位器优先私有方法/字段，优先使用 `selectors.ts` 常量，对外暴露高层业务方法而非底层点击/填写碎方法。
- 测试文件：组织用户故事流程，不散落硬编码 CSS 选择器。前端结构变更时优先改选择器层/POM 层，不直接改业务流程断言。

### 数据类型与最小实现模板

复杂输入定义接口，更新类操作使用可选字段接口：

```ts
export interface UserData {
  email: string
  password: string
  nickname: string
}

export interface UserUpdateData {
  nickname?: string
  password?: string
}
```

`base-page.ts`：

```ts
import { Page, expect } from '@playwright/test'

export class BasePage {
  constructor(protected page: Page) {}

  async goto(path: string): Promise<void> {
    await this.page.goto(path)
    await this.page.waitForLoadState('domcontentloaded')
  }

  async verifyHeading(text: string): Promise<void> {
    await expect(this.page.getByRole('heading', { name: text })).toBeVisible()
  }
}
```

`users-page.ts`（路径以目标项目实际路由为准）：

```ts
import { expect, Page } from '@playwright/test'
import { BasePage } from './base-page'
import { getSelector, SELECTORS } from '../selectors'

export class UsersPage extends BasePage {
  constructor(page: Page) {
    super(page)
  }

  private addButton = () => this.page.locator(getSelector(SELECTORS.buttons.addUser))
  private emailInput = () => this.page.locator(getSelector(SELECTORS.forms.email))
  private submitButton = () => this.page.locator(getSelector(SELECTORS.buttons.submit))

  async gotoUsers(): Promise<void> {
    await this.goto('/users')
  }

  async createUser(email: string): Promise<void> {
    await this.addButton().click()
    await this.emailInput().fill(email)
    await this.submitButton().click()
  }

  async verifyUserExists(email: string): Promise<void> {
    await expect(this.page.getByRole('cell', { name: email })).toBeVisible()
  }
}
```

测试调用：

```ts
test('user flow', async ({ page }) => {
  const users = new UsersPage(page)
  await users.gotoUsers()
  await users.createUser('test@example.com')
  await users.verifyUserExists('test@example.com')
})
```

### 实现边界（AVOID）

- 不在 Page Object 中塞入跨页面业务编排（交给测试层）。
- 不把一次性断言或临时调试逻辑固化到公共页面类。
- 不在测试层直接依赖页面内部 DOM 结构细节。
- 不使用 `waitForTimeout` 代替断言自动等待；不靠瞬时 toast/sonner 作为主验收断言。

## 4. 质量检查清单

- [ ] 关键步骤优先语义化选择器，复杂元素提供稳定 testid 后备，回退链不超过 2 层
- [ ] 共享选择器集中维护在 `selectors.ts`，无类名/深层 DOM 依赖
- [ ] 复杂场景已使用 POM，页面类暴露高层业务方法、私有方法隐藏细节，通用逻辑沉淀到 `BasePage`
- [ ] 使用自动等待断言，不用固定 sleep；主验收断言落在持久状态或稳定结果上
