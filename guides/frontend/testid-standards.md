# data-testid 编写规范（Agent 主规范）

**定位**：本文件是前端 `data-testid` 的唯一主规范。  
**适用对象**：frontend-dev、demo-dev、前端研发人员。

## 核心原则

1. 稳定性优先：避免依赖样式类名、纯文案、DOM 层级。
2. 语义化命名：名称应直接表达业务意图。
3. 一致性：统一使用 kebab-case。
4. 最小必要：仅为有测试价值的元素添加 `data-testid`。

## 命名规范（MANDATORY）

### 基础格式

```text
[entity]-[action]-[type]
```

说明：
- `entity`：对象（`user`、`realm`、`client` 等）
- `action`：动作（`add`、`edit`、`delete`、`search` 等，可省略）
- `type`：组件类型（`button`、`input`、`table`、`dialog` 等）

### 格式约束

- 必须为小写 + 连字符（kebab-case）
- 禁止驼峰、下划线、大写
- 同一页面内必须唯一

正确示例：
- `user-add-button`
- `email-input`
- `user-table`
- `delete-confirm-dialog`

错误示例：
- `userAddButton`
- `email_input`
- `User-Add-Button`

## 覆盖范围分级

| 优先级 | 类型 | 要求 | 示例 |
|---|---|---|---|
| P0 | 可交互元素 | MANDATORY | 按钮、链接、输入框、下拉、复选框 |
| P1 | 数据容器 | MANDATORY | 表格、列表、对话框、关键卡片 |
| P2 | 导航元素 | MANDATORY | 侧边栏、导航链接、分页 |
| P3 | 状态指示 | RECOMMENDED | 加载、错误、空状态、成功提示 |
| P4 | 装饰元素 | AVOID | 图标、分隔线、纯装饰图片 |

## 常用命名模式

| 场景 | 模式 | 示例 |
|---|---|---|
| 输入框 | `{field}-input` | `email-input` |
| 下拉框 | `{field}-select` | `role-select` |
| 复选框 | `{field}-checkbox` | `enabled-checkbox` |
| 提交按钮 | `submit-button` | `submit-button` |
| 取消按钮 | `cancel-button` | `cancel-button` |
| 表格容器 | `{entity}-table` | `user-table` |
| 列表容器 | `{entity}-list` | `realm-list` |
| 导航链接 | `nav-{target}` | `nav-users` |
| 表单对话框 | `{entity}-form-dialog` | `user-form-dialog` |
| 确认对话框 | `{action}-confirm-dialog` | `delete-confirm-dialog` |
| 加载状态 | `loading-spinner` | `loading-spinner` |
| 错误提示 | `error-message` | `error-message` |

## 代码示例

```tsx
<form data-testid="user-form-dialog">
  <input data-testid="email-input" type="email" />
  <select data-testid="role-select">
    <option value="admin">Admin</option>
  </select>
  <button data-testid="submit-button">Submit</button>
</form>
```

## 高频错误

1. 不添加 `data-testid`，导致测试依赖脆弱选择器。
2. 使用无语义命名（如 `btn1`、`button2`）。
3. 多元素复用同一 `data-testid`。
4. 给装饰元素加 testid，增加维护噪音。

## 实施检查清单

- [ ] 使用 kebab-case
- [ ] 命名符合 `{entity}-{action}-{type}`（或省略 action）
- [ ] 页面内 testid 唯一
- [ ] P0/P1/P2 元素已覆盖
- [ ] P3 按需补充
- [ ] 未对 P4 装饰元素添加 testid

## 与选择器策略协同

- 测试优先使用语义化定位；当语义不足或不稳定时使用 `getByTestId`。
- 具体策略见：[Demo 选择器策略主规范](/guides/demo/selector-strategy.md)
