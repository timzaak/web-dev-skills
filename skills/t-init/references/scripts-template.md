# Scripts 模板

本项目不再提供 `dev-start.py` 一键脚本。开发环境请手动启动：

```bash
# 1. 启动 PostgreSQL
docker run -d --name {{PROJECT_NAME}}-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB={{PROJECT_NAME}} \
  -p 5432:5432 \
  postgres:17-alpine

# 2. 启动 Redis
docker run -d --name {{PROJECT_NAME}}-redis \
  -p 6379:6379 \
  redis:7-alpine

# 3. 启动后端
cd backend && cargo run

# 4. 启动前端（另一个终端）
cd frontend && npm run dev
```
