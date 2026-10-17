# Tests To Run Contract

修复角色返回的 `tests_to_run` 每项包含：

- `layer`: `implementation | web-demo`。
- `command`: 目标项目真实可执行命令。
- `reason`: 覆盖的回归风险与选取范围。
- `required`: 布尔值。
- `cwd`: 可选，项目内相对工作目录；省略为项目根目录。

implementation 命令从目标项目脚本、配置、CI 或已确认运行说明中取得，不规定语言、包管理器或测试框架。验证入口不存在、无法运行或选中零用例时报告缺口，不编造命令、不回退到其他技术栈。

web-demo 使用项目本地 `uv run scripts/web-demo-test-runner.py "demo/e2e/<file>.e2e.ts" --run-id <唯一ID>`；脚本缺失时按运行时边界回退插件 runner。项目或 fixture 管理环境时保留 `--no-auto-env`，重跑失败用例追加精确 `--grep`，通过后重跑整文件。

按 implementation -> web-demo 串行补测，去重相同命令；只覆盖实际受影响范围，全量升级须说明原因。编译、类型检查和构建属于静态证据，不能替代所需行为验证。结果记录按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。
