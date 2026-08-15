# Scripts 模板

初始化会在项目根目录生成 `scripts/`。这些脚本是当前项目的运行时入口，可以按项目需要调整 Docker 镜像、容器名、端口和启动命令；脚本文件名和主要参数保持稳定，便于 `/t-tools:t-*` 流程复用。

常用命令：

```bash
# 启动测试依赖（PostgreSQL / Redis / PgDog 等，按 scripts/test-start.py 配置）
uv run scripts/test-start.py

# 运行后端测试
uv run scripts/backend-test.py --

# 停止测试依赖
uv run scripts/test-stop.py

# 运行单个 Demo E2E
uv run scripts/web-demo-test-runner.py demo/e2e/smoke.e2e.ts --mode fast

# 批量运行 Demo E2E（入口由 /t-tools:t-web-demo-run-all 主会话驱动；脚本只辅助发现、进度写盘和汇总）
uv run scripts/web-demo-run-all.py discover
```

如需手动启动开发环境，可直接查看并调整：

- `scripts/test-start.py`
- `scripts/demo-start.py`
- `scripts/demo-stop.py`
