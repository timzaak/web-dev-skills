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
| 页面/组件类型与接线 | `npm run typecheck`，仅证明静态正确性 |
| 状态逻辑、业务操作、小程序 API 接入 | 受影响场景的现有自动化，或微信开发者工具/真机操作验证 |
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

- 未建立独立单测框架时不为此次任务强行引入；类型检查和构建验证静态及打包链路，业务变更按下节取得运行证据
- 页面注册、token 产物、icon manifest、模板文件完整性，优先用构建与 gate 脚本验证
- 不把 Web 前端的 Vitest/MSW/Playwright 规则机械套到 miniapp

## 5. 业务行为验证

- 按本次变更选择最小场景：例如登录后身份恢复、提交后重新进入页面仍能读取结果、导航目标及参数、权限拒绝后的可恢复状态；不把示例当作每次必跑清单。
- 优先复用目标项目已有小程序自动化。没有自动化时，由 dev 或主会话使用微信开发者工具/真机按可复现步骤验证；工具不可用则明确需要人工补充的步骤和结果，不伪造命令或自动化能力。
- 页面交互可先用开发者工具验证；依赖真实设备的授权、相机、扫码等平台行为以对应设备证据为准。H5 构建/预览不能证明微信运行时行为。
- 记录构建版本、工具/设备、数据前提、操作步骤、预期与实际业务结果及截图/日志。完整记录、复用和缺失证据处理按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。
- 不新增 miniapp-demo phase。默认由 miniapp/dev 承担执行、miniapp/accept 核查；需要新增独立测试资产时再规划 miniapp/test。环境或人工结果缺失时保持未验证，不能仅凭 typecheck/build 完成业务验收。

## 6. 相关入口

- 开发主规范：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/development.md`
- 完成前门禁：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/validation.md`
- 验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/quality.md`
- 技术宪法：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/constitution.md`
