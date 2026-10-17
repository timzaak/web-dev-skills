# Shopify 初始化流程

`t-init --shopify <project-name>` 的唯一执行流程。目标：Shopify 官方 React Router 模板 + t-tools 运行设施；不实现业务功能。输出通过 Step 5 后才可作为后续设计/执行的工程基础，静态 smoke 不代表用户故事验收。

项目名称约束与全栈模式相同：仅英文、数字、连字符、下划线；拒绝 `..`、`/`、`\`；长度 1-50 字符。新工程目录采用 CLI 对名称规范化后的 kebab-case，执行前确定并报告实际路径，后续步骤统一使用该路径；已有工程优先匹配用户给出的原目录。

## Step 1: 目录判定

- 目标目录不存在 → 执行 Step 2。
- 已存在且含 `shopify.app.toml` 与 `package.json` → 跳过脚手架，执行 Step 3、Step 4、Step 5；用户本次初始化指令已授权增量补齐，不重复确认。
- 已存在但非完整 Shopify 工程（包括空目录、上次中断的部分产物）→ 不覆盖或删除。报告缺失文件；若能确认是上次脚手架失败，先按 Step 2 的恢复规则修复，否则由用户指定新目录或处理冲突。

## Step 2: Shopify CLI 脚手架（仅新目录）

在目标目录的父目录执行（`--path` 是父目录，不是待创建目录）：

```bash
npm create @shopify/app@latest -- --name <project-name> --template reactRouter --flavor typescript --package-manager npm
```

- 执行前检查当前 CLI 的 Node 要求及 `app init --help`；参数依据 [官方 app init 文档](https://shopify.dev/docs/api/shopify-cli/app/app-init)。不要猜模板标识或把项目名当位置参数。
- CLI 需要登录和组织选择时沿用用户已选账号/组织；非交互环境使用已知的 `--organization-id`。账号、组织未知或浏览器登录不可用时暂停脚手架，报告准确缺项与可执行的手动步骤，不生成虚假 client ID/配置。
- CLI 失败时保留退出码、实际路径及已生成文件清单。参数/依赖问题修正后重试；若已有完整工程则转 Step 3，若已创建远端 App 或部分文件则先核实并恢复关联，不盲目重复创建 App，不自动清理目录。用户完成登录/手动修复后重跑同一入口，由 Step 1 重新判定。
- CLI 成功后确认实际目录、`shopify.app.toml` 和 `package.json`，再进入 Step 3。不自行创建 backend/frontend 骨架。

## Step 3: 增量叠加 t-tools 设施

先读取 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`，再检查已有文件和 git diff。新建、已有工程及中断恢复都遵守同一写入规则：

| 产物 | 缺失 | 已存在 / 重复执行 |
| --- | --- | --- |
| `demo/` 配置、fixture、smoke | 按 3.1 创建 | 复用现有配置和 fixture，只补缺失能力；不替换测试、选择器或日志接线 |
| `scripts/*.py`、`scripts/lib/` | 按 3.2 补齐 | 逐文件比较；相同则跳过，自定义实现保留；接口不兼容时报告具体差异并停止依赖步骤，不整目录覆盖 |
| `AGENTS.md`、README、`scripts/index.md` | 按 3.3 创建 | 读后仅合并缺失说明，不替换用户规则、不重复追加章节；语义冲突交用户裁决 |
| `package.json`、锁文件、`.gitignore` | 创建必要设施文件 | 仅合并缺失依赖/脚本/忽略项；沿用版本与包管理器，不覆盖已有脚本，不因重跑更新全部依赖 |

每步完成后核对实际文件；失败保留已完成产物并报告未完成项。再次调用重新检查内容，仅补齐缺口，不依赖聊天记忆或新增一套初始化状态。

### 3.1 demo/

- 读取 [demo-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/demo-template.md)，沿用其 Playwright + UnifiedLogger 结构，按上表增量生成。安装依赖的工作目录是 `demo/`；已有依赖时不重复添加。
- 新建 smoke 用统一日志 fixture 加 `page.setContent` 渲染本地静态占位内容，不访问 localhost:8080、Shopify 或需要启动服务的页面。已有 smoke 保留，缺少独立日志通路验证时另补初始化 smoke。
- 真实故事的身份 fixture 与业务数据清理由后续 web-demo 按设计实现；环境事实在 Step 4 登记，不编造登录状态或业务测试数据。

### 3.2 scripts/

从 `${CLAUDE_PLUGIN_ROOT}/scripts/` 按增量规则补齐 `web-demo-test-runner.py`、`web-demo-run-all.py`、`web-demo-failure-summary.py`、`cleanup-demo.py`、`cleanup-test-logs.py` 及其 `lib/` 依赖。不新增 `backend-test.py`、`test-start.py`、`test-stop.py`、`demo-start.py`、`demo-stop.py`；已有其他交付端的脚本保留。

在 `scripts/index.md` 登记实际 runner 入口，遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md` 的 Shopify Demo 运行模式；单文件、批量、scan、重试和 continue 均保留 `--no-auto-env`。

### 3.3 根文件

- `AGENTS.md`：仅缺失时使用 [agents-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/agents-template.md)；项目描述为 Shopify App，按增量规则补充规范入口 `${CLAUDE_PLUGIN_ROOT}/guides/shopify/index.md` 和 `scripts/index.md`。保留字面的 `${CLAUDE_PLUGIN_ROOT}` 语义引用，不写本机安装路径。
- `README.md`：合并快速启动和 Demo 手动模式入口，不覆盖模板/项目原有说明。
- `.gitignore`：只增补缺失的日志和 Demo 产物忽略项。
- 读取 [scripts-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/scripts-template.md)，按实际脚本和共享契约生成或合并 `scripts/index.md`。

## Step 4: 账号登录与商家会话环境

读取 [Shopify 本地环境与商家会话](${CLAUDE_PLUGIN_ROOT}/guides/shopify/environment.md)，按其中的方法核验 CLI 登录/关联、适用的代理、商家会话与店面密码环境。

- 将已核实的 org、app/client_id、dev store、admin 预览地址、代理及自动化 Chrome 启动方式登记到 `scripts/index.md`「真实用户故事环境」，附环境变量键位说明和待补齐的业务数据清理入口。
- 凭据只写 `.env.demo`，先确认被 `.gitignore` 忽略；身份 fixture 和具体清理命令留给 web-demo 按设计实现。
- 缺项记录为未就绪，给出用户操作及重跑本步骤的入口；不阻塞 Step 5 的离线设施验证。

## Step 5: 验证与恢复

- 检查根与 `demo/` 的依赖是否就绪；有依赖增量时在各自目录按原包管理器安装。新项目使用 npm，已有项目沿用已有锁文件。
- 优先复用根 `typecheck`，其次 `type-check`。二者都缺失时，基于实际 React Router 配置补充 `typecheck`（通常为 `react-router typegen && tsc --noEmit`），不以裸 `tsc` 省略路由类型生成。已有等价自定义入口可通过上述稳定入口转调；不得覆盖原脚本。
- `build` 必须存在；扩展存在时还需可调用本地 CLI 的 `shopify` 脚本（模板通常为 `shopify`）。缺失时先核实项目实际入口并补齐，不能虚构构建脚本。lint 按已有配置执行，不引入无依据的新 lint 配置。
- 按 `${CLAUDE_PLUGIN_ROOT}/guides/shopify/validation.md` 执行类型检查、应用构建及适用的扩展构建；执行 Demo 类型检查和初始化静态 smoke：`uv run scripts/web-demo-test-runner.py "demo/e2e/smoke.e2e.ts" --no-auto-env`（复用时使用实际 smoke 路径）。缺少 Playwright 浏览器时按项目配置安装后重试。
- 确认 `shopify.app.toml`、`demo/`、5 个脚本及 lib/index、AGENTS/README 齐备。任何必要验证失败或缺工具均记录为未完成/未验证，保留当前产物；修复后重跑 Step 5，不以“文件存在”宣告初始化完成。
- admin 页面、proxy 与扩展的真实店铺冒烟依赖 Step 4；环境缺项时记录为未验证，不计为用户故事验收。

## 收尾输出

- 实际项目路径、模式（新建 / 增量 / 恢复）、新增/合并/保留文件
- 已执行验证、失败或未验证项，以及准确恢复入口
- Step 4 环境就绪情况与待办；custom distribution 沿用用户已确认方案
- Demo 模式与 UnifiedLogger 安装目录
- 初始化验证通过后建议 `/t-decision <feature>`；未通过则先恢复本流程
