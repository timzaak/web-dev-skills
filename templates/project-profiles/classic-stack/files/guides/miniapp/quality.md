# Miniapp 验证与验收规范

在标记 miniapp 任务为完成前取得适用验证证据；`miniapp-accept` 验收前读 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`，公共结论、分级、报告、只读边界和结构化返回只由该协议定义；证据复用按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`；设计适用性按 `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md`。

## 1. 完成前验证清单

1. **类型检查（MANDATORY）**：`cd miniapp && npm run typecheck` —— 0 errors，token/icon 编译链未报错；失败立即修复重跑（最多重试 3 次，仍失败不得标记完成）。
2. **WeChat 构建验证（MANDATORY）**：`cd miniapp && npm run build:weapp` —— 构建成功，页面注册、主题产物、图标 manifest 无阻塞错误（最多重试 3 次）。
3. **H5 预览验证（按需）**：改动跨端共享布局/样式或需核验 H5 预览时运行 `cd miniapp && npm run build:h5`。
4. **模板门禁（按需但推荐）**：变更 token、icon、模板契约或基础设施文件，或需要确认 starter 仍满足发布要求时运行：

```bash
cd miniapp && npm run prepublish:check
cd miniapp && npm run starter:ci-gate -- --target taro-react-taroify-tailwind
```

5. **业务行为验证（行为变更时必须）**：按 `${CLAUDE_PLUGIN_ROOT}/guides/miniapp/testing.md` 执行受影响场景；开发者工具、真机或人工结果缺失时报告未验证及恢复步骤（环境不可用不属于不适用，构建成功不代替业务结果）。

任务完成定义：`typecheck` 与 `build:weapp` 通过、适用的业务行为验证有有效证据、改动涉及的按需验证已执行或明确说明为什么跳过；任一强制验证失败时不得标记完成，必须修复并重新验证，并在完成报告中记录失败与修复过程。

常见阻塞点：新页面在 `src/pages/**` 未注册到 `src/app.config.ts`；token 修改后 `design:build` 产物漂移；业务代码绕过 `AppIcon` 直接引图标库；引入 Web-only 依赖（`react-router-dom`、`Next.js`、`next-themes`、`framer-motion`、`@radix-ui/react-*`）。

## 2. 只读验收依据（miniapp-accept）

### 必要门禁

- 实际项目的 `typecheck`、`build:weapp` 及受影响测试通过。
- 新页面在 `src/app.config.ts` 注册，受影响页面可达；入口符合项目模板（通常为 `src/pages/<page>/index.tsx`）。
- token/icon 产物与受保护文件完整；theme 修改从 `tokens/*.json` 开始，运行时代码消费 `src/theme/` 产物，不把 Tailwind 当作主题真相。
- 图标经 `src/components/AppIcon.tsx` 使用；未引入当前技术线禁用的 Web-only 依赖。
- 本阶段负责的业务场景在微信运行时有有效证据，按 `${CLAUDE_PLUGIN_ROOT}/guides/miniapp/testing.md` 核查设备/工具、关键断言和预期/实际结果。

技术线约束以目标项目事实和明确设计为准，冲突交回主会话，不擅自替换技术方案。目录、组件组织或引用关系整理若无具体契约/行为影响，列维护性改进。

重复代码检查按公共协议触发条件和范围执行，不自动安装扫描工具。报告补充类型/构建、页面注册、主题/图标、受保护文件和业务运行证据；不适用项及后续承接均写清依据。
