# Page Object 更新

适用场景：

- 页面结构变化
- 路由跳转变化
- 表单字段、按钮或对话框行为变化
- 单个测试文件开始堆积重复页面操作

## 处理顺序

1. 定位受影响的 Page Object，优先查看 `demo/e2e/pages/`。
2. 校准对应页面的共享选择器，避免 Page Object 自己发明第二套选择器。
3. 更新页面方法的职责边界：
   - 导航和等待逻辑留在 Page Object
   - 业务断言留在测试文件
4. 用最小测试集验证该页面的主流程。

## 当前常见 Page Object

- `login-page.ts`
- `users-page.ts`
- `roles-page.ts`
- `permissions-page.ts`
- `client-apps-page.ts`
- `settings-page.ts`

## 设计要求

- `goto()` 应反映当前实际路由，如 `/manage/*` 或 `/auth/*`
- `waitForReady()` 只负责页面可交互判定
- 表单填写方法只封装输入动作，不吞掉关键断言
- 如果当前页面已有共享 helper，优先复用，不再复制一份流程

## 完成判定

- 测试文件中的重复 UI 操作减少
- Page Object 没有新增与页面无关的业务判断
- 相关测试在 `--mode fast` 下通过
