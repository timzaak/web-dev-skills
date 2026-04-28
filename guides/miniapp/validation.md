# Miniapp 编译验证步骤

在标记 miniapp 任务为完成前，必须执行以下验证。

## 验证清单

### 1. 类型检查（MANDATORY）

```bash
cd miniapp && npm run typecheck
```

验收标准：
- 类型检查通过（0 errors）
- token/icon 编译链未报错

如果失败：
1. 分析 TypeScript、token、icon 或导入错误
2. 立即修复
3. 重新执行 `npm run typecheck`
4. 最多重试 3 次
5. 仍然失败则不能标记完成

### 2. WeChat 构建验证（MANDATORY）

```bash
cd miniapp && npm run build:weapp
```

验收标准：
- `weapp` 构建成功
- 页面注册、主题产物、图标 manifest 无阻塞错误

如果失败：
1. 分析构建、页面注册、token 编译或平台兼容错误
2. 立即修复
3. 重新执行 `npm run build:weapp`
4. 最多重试 3 次

### 3. H5 预览验证（按需）

以下场景建议执行：
- 改动了跨端共享布局或样式
- 需要核验 H5 预览行为

```bash
cd miniapp && npm run build:h5
```

### 4. 模板门禁（按需但推荐）

以下场景建议执行：
- 变更了 token、icon、模板契约或基础设施文件
- 需要确认 starter 仍满足发布要求

```bash
cd miniapp && npm run prepublish:check
cd miniapp && npm run starter:ci-gate -- --target taro-react-taroify-tailwind
```

## 任务完成定义

只有在以下条件满足时，才能标记 miniapp 任务为完成：
- `npm run typecheck` 通过
- `npm run build:weapp` 通过
- 改动涉及的按需验证已执行或明确说明为什么跳过

如果任何强制验证失败：
- 不能标记完成
- 必须修复并重新验证
- 在完成报告中记录失败与修复过程

## 常见阻塞点

### 1. 页面未注册

新页面位于 `src/pages/**` 但未同步到 `src/app.config.ts`。

### 2. 主题产物漂移

修改了 token 或 theme 相关代码，但 `design:build` 产物不一致或引用断裂。

### 3. 图标入口绕过

业务代码直接引用图标资产或其他图标库，而不是 `AppIcon`。

### 4. 引入 Web-only 依赖

引入 `react-router-dom`、`next-themes`、`framer-motion`、`@radix-ui/react-*` 等不符合 miniapp 技术线的库。
