# Miniapp 验收依据

验收前读 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`，公共结论、分级、报告、只读边界和结构化返回只由该协议定义。设计适用性按 `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md`。

## 必要门禁

- 实际项目的 `typecheck`、`build:weapp` 及受影响测试通过。
- 新页面在 `src/app.config.ts` 注册，受影响页面可达；入口符合项目模板（通常为 `src/pages/<page>/index.tsx`）。
- token/icon 产物与受保护文件完整；theme 修改从 `tokens/*.json` 开始，运行时代码消费 `src/theme/` 产物，不把 Tailwind 当作主题真相。
- 图标经 `src/components/AppIcon.tsx` 使用；未引入当前技术线禁用的 Web-only 依赖，如 `react-router-dom`、`next-themes`、`framer-motion`、`@radix-ui/react-*`。
- 本阶段负责的业务场景在微信运行时有有效证据，按 `${CLAUDE_PLUGIN_ROOT}/guides/miniapp/testing.md` 核查设备/工具、关键断言和预期/实际结果；构建不代替业务运行。

技术线约束以目标项目事实和明确设计为准，冲突交回主会话，不擅自替换技术方案。目录、组件组织或引用关系整理若无具体契约/行为影响，列维护性改进。

## 命令与专项检查

从项目配置确认入口并复用有效证据；补跑时限定受影响范围：

```bash
cd miniapp && npm run typecheck
cd miniapp && npm run build:weapp
```

仅命中相应交付面或项目门禁时执行 `build:h5`、`prepublish:check`、`starter:ci-gate -- --target taro-react-taroify-tailwind`。重复代码检查按公共协议的触发条件和范围执行，不自动安装扫描工具。

报告补充类型/构建、页面注册、主题/图标、受保护文件和业务运行证据；不适用项及后续承接均写清依据。
