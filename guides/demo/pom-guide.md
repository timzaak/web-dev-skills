# Page Object Model (POM) 使用指南（精简版）

**目的**：定义 Demo/E2E 中 POM 的最小实现规范，提升可维护性。

**目标读者**：测试开发人员、demo-dev agent、测试维护人员

---

## 何时使用 POM（决策表）

| 场景复杂度 | 参考规模 | 方案 |
|---|---|---|
| 简单 | < 50 行 | 可直接写测试 |
| 中等 | 50-200 行 | 使用选择器常量 |
| 复杂 | > 200 行或跨页面流程 | MANDATORY：使用 POM |

触发 POM 的典型信号：
- 选择器在多个测试重复出现
- 同一页面操作在多个场景复用
- 单文件维护成本明显升高

---

## 架构约定（MANDATORY）

### 文件结构

```text
demo/e2e/
├── pages/
│   ├── base-page.ts
│   ├── users-page.ts
│   └── ...
├── selectors.ts
└── [role]/*.e2e.ts
```

### 职责划分

- `BasePage`：通用能力（导航、通用等待、通用断言）
- `XxxPage`：页面级业务操作与页面级断言
- 测试文件：组织用户故事流程，不直接管理底层选择器

### 选择器约束

- Page Object 内必须优先使用 `selectors.ts` 常量
- 禁止在测试文件中散落硬编码 CSS 选择器

---

## 接口与方法规范

### Page 类设计

- 类名：`XxxPage`
- 文件名：`xxx-page.ts`
- 页面元素定位器：优先私有方法/字段
- 对测试暴露"高层业务方法"，避免只暴露底层点击/填写碎方法

### 数据类型

- 复杂输入必须定义接口
- 更新类操作使用可选字段接口

示例：

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

---

## 最小实现模板

### `base-page.ts`

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

### `users-page.ts`

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
    await this.goto('/manage/users')
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

### 测试调用（最小）

```ts
test('user flow', async ({ page }) => {
  const users = new UsersPage(page)
  await users.gotoUsers()
  await users.createUser('test@example.com')
  await users.verifyUserExists('test@example.com')
})
```

---

## 实现边界（AVOID）

- 不在 Page Object 中塞入跨页面业务编排（交给测试层）
- 不把一次性断言或临时调试逻辑固化到公共页面类
- 不在测试层直接依赖页面内部 DOM 结构细节

---

## 质量检查清单

- [ ] 复杂场景已使用 POM
- [ ] 选择器通过 `selectors.ts` 统一管理
- [ ] 页面类暴露高层业务方法
- [ ] 私有方法隐藏实现细节
- [ ] 复杂输入已定义接口
- [ ] 通用逻辑沉淀到 `BasePage`
- [ ] 测试文件仅表达用户故事流程
- [ ] 未出现明显重复选择器/重复页面操作实现
