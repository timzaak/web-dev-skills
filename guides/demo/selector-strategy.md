# Demo 选择器策略（Agent 主规范）

**定位**：本文件是 Demo/E2E 选择器策略的唯一主规范。
**适用对象**：demo-dev、frontend-dev、测试维护人员。

## 复杂度决策（MANDATORY）

| 复杂度 | 参考规模 | 推荐方案 |
|---|---|---|
| 简单 | < 50 行 | 可直接写测试 |
| 中等 | 50-200 行 | 使用 `selectors.ts` 集中管理 |
| 复杂 | > 200 行或跨页面流程 | 必须使用 POM |

## 选择器优先级（MANDATORY）

| 优先级 | 类型 | 使用条件 | 备注 |
|---|---|---|---|
| 1 | `getByRole` | 有明确语义角色与可访问名称 | 首选 |
| 2 | `getByLabel` / `getByPlaceholder` | 表单可见属性可稳定定位 | 表单优先 |
| 3 | `getByTestId` | 复杂组件、语义不足、文案不稳定 | 稳定后备 |
| 4 | `getByText` | 临时或低风险场景 | 注意国际化与歧义 |
| 5 | `locator(css/xpath)` | 上述都不可用时 | 需在代码旁说明原因 |

AVOID：
- 依赖样式类名（如 `.btn-primary`）
- 依赖深层 DOM 路径（如 `div > div:nth-child(2)`）
- 全局无约束文本匹配

## 决策流程

1. 能用 `getByRole` 则直接使用。
2. 表单元素优先 `getByLabel` / `getByPlaceholder`。
3. 语义弱或文本不稳定时使用 `getByTestId`。
4. 必须使用 CSS/XPath 时，限制作用域并记录原因。

## 与 data-testid 协同

- `data-testid` 不是默认第一选择，但必须为关键交互准备稳定后备。
- 以下场景推荐直接使用 `getByTestId`：
  - 第三方组件语义不完整
  - 自定义复杂组件缺少稳定语义
  - 文案频繁变化或多语言差异较大

## 共享选择器与回退链

建议在 `demo/e2e/selectors.ts` 管理共享选择器：

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

约束：
- 主选择器必须是当前最稳定方案。
- 后备选择器最多 1-2 个。
- 禁止堆叠过多回退链掩盖真实问题。

## POM 约束

- 复杂测试必须使用 POM。
- 共享选择器必须集中在 `selectors.ts`，禁止在测试文件散落硬编码。
- 前端结构变更时优先改选择器层/POM 层，不直接改业务流程断言。

## 常见反模式

1. 使用 `waitForTimeout` 代替断言自动等待。
2. 测试文件中重复硬编码选择器。
3. 关键路径只靠文本定位，文案变更即失败。
4. 使用不可维护的 CSS 链式路径。
5. 选择器无法表达业务意图。

## 质量检查清单

- [ ] 关键步骤优先语义化选择器
- [ ] 复杂元素提供稳定 testid 后备
- [ ] 共享选择器集中维护
- [ ] 关键路径无类名/深层 DOM 依赖
- [ ] 使用自动等待断言，不用固定 sleep
- [ ] 回退链不超过 2 层
