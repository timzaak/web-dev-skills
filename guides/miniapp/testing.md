# 小程序测试与构建规范

本页只回答 miniapp 应该跑哪些验证，不重述实现架构。

## 1. 目标

miniapp 当前的测试与验证重点是：
- TypeScript 类型正确性
- token/icon 编译链完整性
- `weapp` 构建可通过
- 模板契约与发布前门禁可通过

## 2. 推荐验证层级

| 需求类型 | 首选验证 |
| --- | --- |
| 页面/组件实现、状态逻辑、小程序 API 接入 | `npm run typecheck` |
| 真实交付链路、页面注册、资源编译 | `npm run build:weapp` |
| H5 预览相关问题 | `npm run build:h5` |
| 模板完整性、starter 契约、受保护文件漂移 | `npm run prepublish:check` / `npm run starter:ci-gate -- --target taro-react-taroify-tailwind` |

## 3. 当前命令入口

```bash
cd miniapp
npm run typecheck
npm run build:weapp
npm run build:h5
npm run prepublish:check
npm run starter:ci-gate -- --target taro-react-taroify-tailwind
```

说明：
- `typecheck` 和 `build:*` 会先触发 `design:build`
- `design:build` 会执行 token 编译、icon 构建和 generated 内容格式化

## 4. 测试边界

- 当前仓库未建立独立的小程序单元测试框架时，优先用类型检查与构建验证保证回归
- 页面注册、token 产物、icon manifest、模板文件完整性，优先用构建与 gate 脚本验证
- 不把 Web 前端的 Vitest/MSW/Playwright 规则机械套到 miniapp

## 5. 相关入口

- 开发主规范：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/development.md`
- 完成前门禁：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/validation.md`
- 验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/quality.md`
- 技术宪法：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/constitution.md`
