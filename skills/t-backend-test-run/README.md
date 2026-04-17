# t-backend-test-run Skill

自动化后端测试运行和错误修复的工作流。

## 功能

- 🔍 智能分析代码变更，确定需要运行的测试
- 🎯 使用 nextest filtersets 精准运行测试
- 📋 自动捕获和分类所有错误
- 🛠️ 创建优先级修复计划
- 🤖 调用 `backend-dev` subagent 逐个修复
- ✅ 重新测试验证修复效果
- 📚 冲突时查阅 PRD/用户故事
- 🔗 作为 `/t-run` 的 `backend-test` 默认执行路径，以及 `/t-task` 生成 `backend/test.md` 时的默认约束

## 使用方式

### 直接触发

当你说以下内容时，Claude 会自动使用这个 skill：

- "运行后端测试"
- "修复测试失败"
- "uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py"
- "测试挂了，帮我看看"
- "验证一下后端代码"

### 典型工作流

```bash
# 1. 修改代码后
git status

# 2. Claude 自动分析变更
# 3. 运行相关测试
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(points)'

# 4. 如果有错误，自动修复
# 5. 重新测试验证
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(points)'
```

## Nextest 过滤示例

```bash
# 特定测试
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- test_points_deduction

# 特定包
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(points)'

# 组合过滤
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(api) and test(webhook)'

# 排除测试
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'not test(slow)'
```

## 核心特性

### 1. 智能测试选择
根据代码变更自动确定测试范围：
- 单文件修改 → 精准测试
- 模块修改 → 包级测试
- 多处局部修改 → 组合 filterset
- 影响范围无法可靠收敛 → 记录原因后升级全量测试

### 2. 错误分类
- 编译错误（优先修复）
- 运行时错误
- 断言失败
- 基础设施问题

### 3. 冲突解决
当测试和实现不一致时：
1. 查阅 `docs/user-stories/`
2. 查阅 `docs/prd/`
3. 决定修复测试还是实现
4. 记录决策依据

### 4. 自动修复
- 调用 `backend-dev` subagent
- 逐个修复错误
- 验证每个修复
- 生成修复报告

## 默认原则

- 默认先做定向测试，不直接跑全量 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`
- 全量测试只在用户明确要求，或影响范围无法可靠界定时才执行
- 生产代码修复优先交给 `backend-dev`，测试层只处理自身拥有的测试问题

## 文件位置

- Skill: `skills/t-backend-test-run/SKILL.md`
- 测试脚本: `scripts/backend-test.py`
- 测试日志: `backend-test-output.log`

## 相关文档

- [后端开发规范](/spec/backend/development.md)
- [环境与测试指南](/spec/core/environment-and-testing-guide.md)
