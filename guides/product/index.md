# Product 规范入口

product 规范入口，按“先区分 user story 和 PRD，再进入对应约束页”使用。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| 用户故事写法、INVEST 原则与 GWT 验收标准 | [user-story.md](/guides/product/user-story.md) |
| PRD 的职责边界、推荐结构和禁止内容 | [prd.md](/guides/product/prd.md) |

## 使用规则

- `user-story.md` 只定义用户行为与价值表达，不承载接口、数据库或实现细节。
- `prd.md` 只定义产品边界、规则和验收目标，不替代技术设计文档。
- `/t-prd` 和 `/t-prd-check` 应优先引用本入口，再按需进入具体页面。
