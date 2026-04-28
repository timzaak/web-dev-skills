# 小程序开发规范

当前 `miniapp/` 的事实型主规范。只描述仓库现状、稳定约束和最低验证，不承担 Taro 或 Taroify 的教学职责。

## 1. 文档定位

本页保留：
- 当前 miniapp 的技术基线、目录职责和页面注册事实
- token、theme、icon、模板契约的稳定约束
- 完成前最低验证命令

本页不展开：
- Taro 语法教学
- 某个 feature 的局部实现 recipe
- 详细测试与验收清单

相关入口：
- miniapp 规范入口：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/index.md`
- 测试规则：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/testing.md`
- 完成前验证：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/validation.md`
- 验收与模板门禁：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/quality.md`
- 技术宪法：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/constitution.md`
- 执行约束：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/ai-rules.md`

## 2. 当前技术基线

`miniapp/package.json` 当前可确认的主栈：

- Taro 4
- React 18 + TypeScript 5
- Taroify
- Tailwind CSS 4
- weapp-tailwindcss
- Style Dictionary
- Tokens Studio transforms
- Iconify 离线图标构建

补充事实：
- `npm run typecheck` 当前会先执行 `npm run design:build`，再执行 `tsc --noEmit`
- `npm run build:weapp` 与 `npm run build:h5` 当前都会先执行 `npm run design:build`

## 3. 当前目录与职责

以 `miniapp/` 当前实现为准：

| 路径 | 当前职责 |
| --- | --- |
| `src/app.tsx` | 小程序应用入口 |
| `src/app.config.ts` | 页面注册真相 |
| `src/pages/` | 页面入口文件 |
| `src/components/` | 共享组件与基础包装 |
| `src/theme/` | token 编译产物、主题 CSS、图标 manifest、Taroify 主题映射 |
| `src/styles/` | Tailwind 入口与共享样式 |
| `tokens/` | 设计 token 源文件，主题唯一真相 |
| `scripts/` | token、icon、模板门禁脚本 |
| `config/` | Taro 构建配置 |

## 4. 页面与路由事实

稳定事实：
- 新页面放在 `src/pages/<page>/index.tsx`
- 新页面必须在 `src/app.config.ts` 注册
- `src/app.config.ts` 是页面注册唯一真相
- 当前仓库的 miniapp 是独立于 `frontend/` 的交付线，不复用 React Router

## 5. 主题、token 与 icon 约束

- `tokens/*.json` 是主题唯一真相
- 运行时代码消费 `src/theme/` 中的编译结果，而不是直接读取 token 源文件
- Tailwind 只用于布局和组合效率，不是主题真相
- `src/components/AppIcon.tsx` 是业务代码使用图标的唯一入口
- 不直接在业务页面里引入 `@taroify/icons`、运行时 Iconify 包或散落的 SVG 组件
- 对 theme/token 的修改应从 `tokens/*.json` 开始，而不是手改编译产物

## 6. 当前实现边界

以下内容不视为 miniapp 主规范的默认事实：

- 可以使用 `react-router-dom`、`next-themes`、`framer-motion` 等 Web-only 依赖
- 可以让 Tailwind 成为主题系统主来源
- 可以绕过 `AppIcon` 直接接入第二套图标系统
- 可以把 `src/theme/` 手工维护成业务逻辑目录

如某个 feature 需要特殊模板扩展、平台差异处理或局部构建技巧，应写到该 feature 设计文档、测试文档或具体实现附近，而不是回写成 miniapp 全局主规范。

## 7. 受保护文件与可编辑区

优先编辑区域：
- `src/pages/**`
- `src/components/**`
- `src/services/**` 或 `src/utils/**`（如引入）
- `src/store/**`（如引入）

默认受保护文件：
- `config/index.js`（注意：当前为 JS 文件，非 TS）
- `src/app.config.ts`
- `package.json`
- `project.config.json`
- `tailwind.config.ts`
- `style-dictionary.config.mjs`
- `tokens/*.json`
- `scripts/build-icons.mjs`
- `src/theme/taroify-theme.ts`
- `src/theme/icons/manifest.ts`
- `template.config.json`

未经明确需求，不修改这些基础设施文件。

## 8. 完成前最低验证

```bash
cd miniapp
npm run typecheck
npm run build:weapp
```

如需更完整的 H5 预览、模板门禁或发布前检查，按 `${CLAUDE_PLUGIN_ROOT}/guides/miniapp/testing.md`、`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/validation.md` 和 `${CLAUDE_PLUGIN_ROOT}/guides/miniapp/quality.md` 执行。
