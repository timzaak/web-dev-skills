# 小程序开发规范

Miniapp 主规范。它定义插件级稳定约束；目标项目的真实目录、页面注册、主题和构建脚本以目标项目代码与 `docs/`、`.ai/` 产物为准。

## 1. 文档定位

本页保留：
- miniapp 技术基线、目录职责和页面注册事实的确认方法
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

先读取目标项目的 `miniapp/package.json`、Taro 配置、页面注册文件、主题/token 配置和现有页面代码，确认真实技术栈。默认模板倾向以下组合，但不得覆盖目标项目事实：

- Taro
- React + TypeScript
- Taroify
- Tailwind CSS
- weapp-tailwindcss
- Style Dictionary
- Tokens Studio transforms
- Iconify 离线图标构建

类型检查、设计 token 构建和小程序构建命令以 `miniapp/package.json` scripts 为准。

## 3. 当前目录与职责

以目标项目 `miniapp/` 当前实现为准。先确认应用入口、页面注册、页面目录、共享组件、服务层、主题/token、脚本和 Taro 配置的实际落点，再写入或修改文件。

## 4. 页面与路由事实

稳定事实：
- 新页面位置和注册方式以目标项目现有页面结构为准。
- 页面注册文件是页面可达性的唯一真相，修改页面时必须同步检查。
- miniapp 是独立于 Web `frontend/` 的交付线，不复用 React Router。

## 5. 主题、token 与 icon 约束

- 主题 token 源文件是主题唯一真相，具体路径以目标项目配置为准。
- 运行时代码消费已编译的主题结果，而不是直接读取 token 源文件。
- Tailwind 只用于布局和组合效率，不是主题真相
- 图标入口以目标项目现有封装为准。
- 不直接在业务页面里引入 `@taroify/icons`、运行时 Iconify 包或散落的 SVG 组件
- 对 theme/token 的修改应从 token 源文件开始，而不是手改编译产物。

## 6. 当前实现边界

以下内容不视为 miniapp 主规范的默认事实：

- 可以使用 `react-router-dom`、`next-themes`、`framer-motion` 等 Web-only 依赖
- 可以让 Tailwind 成为主题系统主来源
- 可以绕过 `AppIcon` 直接接入第二套图标系统
- 可以把主题编译产物目录手工维护成业务逻辑目录

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
