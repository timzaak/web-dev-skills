---
name: t-prd-check
description: Validate PRD, HTML Preview, and user stories for quality and consistency.
argument-hint: "[feature-name|--all]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Bash
---

# PRD & User Story Quality Check

运行时边界统一参考：`protocols/runtime-boundaries.md`

## 目标
- 验证 PRD 文档完整性和规范性
- 检查 PRD HTML Preview 的存在性、可审阅性和 PRD 一致性
- 评估用户故事质量（INVEST 原则、GWT 格式）
- 检查 PRD 与用户故事的一致性
- 检查 PRD / 用户故事是否错误混入接口、建表、schema 等实现细节
- 输出量化评分和修复清单

评分、扣分和问题分级统一参考：`protocols/prd-check-rubric.md`

## 使用方式
```bash
/t-prd-check [feature-name]
/t-prd-check --all
```

## 输入范围
- PRD 文档: `docs/prd/**/*.md`（排除 `00-index.md`）
- PRD HTML Preview: `.ai/preview/**/*.html`
- 用户故事: `docs/user-stories/**/*.md`
- 排除文件: `00-index.md`, `_roles.md`, `_README.md`, `client-app-settings.md`, `builtin_protection.md`

## 执行流程

### 1. 确定检查范围
- 解析命令参数，确定单功能或全量检查
- 使用 `Glob` 发现目标文件并排除特殊文件

### 2. 读取角色定义
- 读取 `docs/user-stories/_roles.md`
- 解析角色名称和技术标识，用于校验故事中的角色引用

### 3. PRD 检查
按 `protocols/prd-check-rubric.md` 执行：

- 基础章节检查
- 用户故事引用检查
- PRD 分层与禁止内容检查

### 4. HTML Preview 检查
按 `protocols/prd-preview-contract.md` 执行：

- 先运行 `${CLAUDE_PLUGIN_ROOT}/scripts/check-prd-preview.py [feature-name|--all] --root . --json` 获取机械检查结果
- 检查 `.ai/preview/<domain>/<feature>.html` 是否存在
- 检查 Preview 是否为目标技术栈无关的单文件 HTML
- 检查 Preview 是否包含来源 PRD 路径和固定审阅区域
- 对前端/交互功能，检查 Preview 是否聚焦 PRD 定义的目标体验和关键状态，而不是复刻现有代码已经具备的 UI
- 检查 Preview 是否没有引入 PRD 未声明的新业务规则、权限规则或验收目标
- 检查 Preview 与 Markdown PRD 在目标、范围、流程、业务状态、规则和验收目标上是否描述一致
- 检查 Preview 是否没有混入端点、schema、建表、迁移或类型定义
- 检查示例数据和待确认假设是否显式标注
- 将脚本发现的问题并入 P0/P1/P2 问题清单；脚本无法判断的 PRD 语义一致性继续人工/模型检查

### 5. 用户故事检查
按 `protocols/prd-check-rubric.md` 执行：

- 故事结构检查
- INVEST 原则检查
- 禁止内容检测
- 新文档质量门禁检查

### 6. 一致性检查
- 检查 PRD 中的用户故事链接是否有效
- 比较 PRD 与用户故事中的优先级是否一致
- 校验用户故事中的角色是否存在于 `_roles.md`
- 比较 HTML Preview 与 PRD 的关键规则、流程、状态和验收目标是否一致

### 7. 评分计算
按 `protocols/prd-check-rubric.md` 计算：

- `PRD Score`
- `User Story Score`
- `Consistency Score`
- `Preview Score`
- `Total Score`

### 8. 问题分级
问题分级统一参考：`protocols/prd-check-rubric.md`

### 9. 输出要求
- 控制台摘要和报告结构统一参考：`protocols/prd-check-rubric.md`
- 详细报告文件：`.ai/quality/prd-check-[YYYYMMDD-HHMMSS].md`

### 10. 失败处理
- 未找到文档：提示检查功能名称或改用 `--all`
- 文件解析错误：记录错误并继续其他文件
- 报告目录不存在：使用 `Bash` 创建 `.ai/quality/`
- Preview 脚本不可执行或 Python 不可用：记录为检查阻塞项，不跳过 HTML Preview 语义检查

### 11. 相关引用
- `protocols/runtime-boundaries.md`
- `protocols/prd-check-rubric.md`
- `protocols/prd-preview-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/scripts/check-prd-preview.py`
- `${CLAUDE_PLUGIN_ROOT}/guides/product/index.md` - product guide 入口
- `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` - 用户故事规范和 INVEST 原则
- `${CLAUDE_PLUGIN_ROOT}/guides/product/prd.md` - PRD 分层与禁止内容规范
- `docs/user-stories/_roles.md` - 角色定义
- `skills/t-dream/SKILL.md` - PRD 等描述与实现事实准确性排查入口
