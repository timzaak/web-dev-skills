# Miniapp Agent 质量验收规范

## 1. 适用范围

适用于 `miniapp/` 代码变更的验收，包括：
- 类型安全与构建质量
- 页面注册与模板完整性
- theme/token/icon 体系约束
- 小程序技术线合规

## 2. 前置检查（MANDATORY）

先完成设计一致性检查：
- 参考 `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md`
- 读取 `.ai/design/[任务名].md`
- 豁免前缀：`bugfix-`、`refactor-`、`doc-`、`test-`、`style-`

## 3. 验收门禁

### P0（必须通过）
- `npm run typecheck` 通过
- `npm run build:weapp` 通过
- 新页面已在 `src/app.config.ts` 正确注册
- token/icon 产物无阻塞缺失
- 关键受保护文件未被无依据破坏

### P1（应通过）
- 未把 Tailwind 当作主题真相
- 图标统一经 `AppIcon` 使用
- 未引入禁用的 Web-only 依赖
- token、theme、icon 引用关系保持清晰

### P2（可改进）
- 组件拆分、目录组织、可维护性优化

## 4. 执行步骤与命令

```bash
cd miniapp
npm run typecheck
npm run build:weapp
```

按需执行：

```bash
cd miniapp && npm run build:h5
cd miniapp && npm run prepublish:check
cd miniapp && npm run starter:ci-gate -- --target taro-react-taroify-tailwind
```

## 5. 核对重点

- 页面入口文件是否位于 `src/pages/<page>/index.tsx`
- `src/app.config.ts` 是否与页面变更一致
- theme 修改是否从 `tokens/*.json` 开始，而不是散落到业务代码
- 运行时代码是否消费 `src/theme/` 编译结果
- 图标是否统一经 `src/components/AppIcon.tsx`
- 是否误引入 `react-router-dom`、`next-themes`、`framer-motion`、`@radix-ui/react-*` 等禁用依赖

## 6. 报告与判定

输出文件：`.ai/quality/check-[date].md`

### 状态
- `ACCEPTED`：P0/P1 全部通过
- `REJECTED`：任一 P0 失败
- `ACCEPTED WITH IMPROVEMENTS`：P0 全通过，存在 P2 改进项

### 报告最小字段
- 类型检查、构建、模板门禁结果
- 页面注册与主题/图标约束检查结果
- 风险与修复建议（P0/P1/P2）

## 7. 禁止行为

- 未经授权修改代码
- 只读验收默认禁止执行会改写仓库文件的命令
- 禁止无证据结论
