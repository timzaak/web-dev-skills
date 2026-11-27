# 后端测试指南

适用于目标项目的 Rust 后端测试。

## 入口

后端测试统一使用目标项目内脚本入口：

```bash
uv run scripts/backend-test.py -- [filter]
```

需要显式复用环境时：

```bash
uv run scripts/test-start.py
uv run scripts/backend-test.py --
uv run scripts/test-stop.py
```

## 项目事实确认

- 后端 workspace 真相以 `backend/Cargo.toml` 为准。
- 测试隔离以目标项目现有 test helper、fixture、schema 或 database 隔离实现为准。
- 真实数据库结构只来自目标项目迁移目录。
- 路由断言、租户参数和鉴权前提以当前真实接口与设计文档为准。

## 编写规则

- 场景测试优先覆盖跨模块流程、数据库交互和 HTTP 主链路。只有场景测试难稳定覆盖且有回归风险时，单元测试才覆盖业务规则、边界条件、状态转换、权限判断、错误映射、数据规范化或核心算法；新增前说明可观察回归和覆盖缺口。
- 不为只做字段赋值的 struct `new()`/builder/getter/setter、DTO/derive-only 类型、常量、简单 enum、机械字段映射或第三方库保证行为编写单元测试。
- 允许不新增单元测试；若改动只是 DTO、路由注册、字段透传或 OpenAPI 注解，优先用编译、定向场景测试或 OpenAPI 生成验证覆盖。
- 场景测试统一优先复用测试上下文和统一测试路由入口。
- 不在测试代码里维护第二套 DDL；需要结构变更时先改 migration。
- 路由断言与示例应使用当前真实接口路径，不沿用历史项目中的旧路径。

## 高价值局部测试与按需 TDD

仅在已确认重要覆盖缺口且普通场景测试难稳定覆盖时使用局部测试，不因 Domain/Application 分层要求逐层补单测：

- **只替换必要的外部边界**：例如恢复令牌在截止时刻失效时，若项目已有可注入时钟，只替换时钟验证截止前可恢复、截止时返回明确过期错误且不消耗令牌或改变业务状态，不 mock 整条业务链路。
- **不引入过度抽象**：不为测试引入本次生产需求不需要的 Repository 抽象、复杂 mock 框架或多层 fixture，准备成本高于覆盖收益时回到场景验证评估；不得仅以 `result.is_ok()` 或 mock 调用次数证明普通创建流程正确。
- **按需 Red-Green-Refactor**：测试先行能澄清规则时，先写能暴露缺陷的最小失败用例，再实现并定向验证；同一规则的等价边界表驱动合并，不为每个内部方法生成一个用例；未改变可观察行为的重构保留断言，仅在相关实现或测试变化后重跑。
- **交付要求**：本次新增或修改的单测必须实际通过；运行证据记录与验收复用按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。

## 验证

常用命令：

```bash
# 全量后端测试
uv run scripts/backend-test.py --

# 按测试名或 pattern 定向执行
uv run scripts/backend-test.py -- test_scenario

# 运行最近失败的测试
uv run scripts/backend-test.py -- -R latest

# 使用 nextest 表达式收敛范围
uv run scripts/backend-test.py -- -E 'package(<crate>) and test(<pattern>)'
```

`[filter]` 是传给底层测试运行器的可选参数；没有 filter 时命令就是 `uv run scripts/backend-test.py --`。

格式与静态检查收口：

```bash
cd backend
/t-tools:t-review
cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features
cargo fmt --all
```

## 参考

- 环境与测试总览：[`environment-and-testing-guide.md`](${CLAUDE_PLUGIN_ROOT}/guides/core/environment-and-testing-guide.md)
- 后端开发规范：[`development.md`](${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md)
- Backend 验收：[`quality.md`](${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md)
