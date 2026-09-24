# 后端高价值局部测试与按需 TDD

仅在已按 `${CLAUDE_PLUGIN_ROOT}/guides/backend/testing.md` 确认重要覆盖缺口后读取。普通 HTTP/数据库成功路径优先使用场景测试，不因 Domain/Application 分层要求逐层补单测。

## 选择局部测试

新增前说明：要防止的可观察回归、已有场景测试为什么难以稳定覆盖，以及本次最小断言。构造赋值、DTO、getter/setter、机械映射和第三方库保证的行为不构成补测理由。

适用示例：项目规定恢复令牌在截止时刻失效，但 HTTP 场景难稳定命中精确时间边界。若项目已有可注入时钟，局部用例验证截止前可恢复、截止时返回明确过期错误，且失败不会消耗令牌或改变业务状态。只替换时钟这一外部边界，断言实际业务结果，不 mock 整条业务链路。

不要为了测试引入本次生产需求不需要的 Repository 抽象、复杂 mock 框架或多层 fixture。若准备成本高于覆盖收益，回到场景验证评估；不得仅以 `result.is_ok()` 或 mock 调用次数证明普通创建流程正确。

## 按需 Red-Green-Refactor

- 已确认局部测试有价值，且测试先行能澄清规则时，先写能暴露该缺陷的最小失败用例，再实现并定向验证。
- 未改变可观察行为的重构保留断言；仅在相关实现或测试变化后重跑，不为编辑了无关文件重复运行。
- 同一规则的等价边界可表驱动合并；不为每个内部方法生成一个用例。

## 执行与交付

命令使用目标项目统一入口及真实 package/module：

```bash
uv run scripts/backend-test.py -- -E 'package(<core-package>) and test(<rule-pattern>)'
```

本次新增或修改的单测必须实际通过。无增量价值时不新增，按任务安排验证已有受影响测试和业务场景。运行证据记录与验收复用按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`；测试选择和命令入口以 testing.md 为准。
