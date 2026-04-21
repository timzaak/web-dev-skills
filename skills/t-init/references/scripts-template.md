# Scripts 模板

## 1. scripts/dev-start.py

```python
#!/usr/bin/env python
"""
开发环境启动脚本

自动启动所有依赖服务和开发服务器：
1. PostgreSQL (Docker)
2. Redis (Docker)
3. Backend (cargo run)
4. Frontend (npm run dev)

使用方式：
  python scripts/dev-start.py           # 复用已有容器
  python scripts/dev-start.py --clean   # 重建容器（清空数据）

前置条件：
  - Docker 已安装并运行
  - cargo 已安装
  - npm 已安装
"""
import subprocess
import sys
import os

PROJECT_NAME = "{{PROJECT_NAME}}"
BACKEND_PORT = 8080
FRONTEND_PORT = 3000
POSTGRES_PORT = 5432
REDIS_PORT = 6379

def run_cmd(cmd, **kwargs):
    """运行命令并实时输出"""
    print(f"→ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    return subprocess.run(cmd, **kwargs)

def docker_container_exists(name):
    """检查 Docker 容器是否存在"""
    result = subprocess.run(
        ["docker", "ps", "-a", "-q", "-f", f"name={name}"],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())

def docker_rm(name):
    """删除 Docker 容器"""
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    pg_name = f"{PROJECT_NAME}-dev-postgres"
    redis_name = f"{PROJECT_NAME}-dev-redis"

    # 启动 PostgreSQL（复用已有容器，加 --clean 参数重建）
    if docker_container_exists(pg_name):
        if "--clean" in sys.argv:
            print(f"Removing existing PostgreSQL container...")
            docker_rm(pg_name)
        else:
            print(f"Starting existing PostgreSQL container...")
            subprocess.run(["docker", "start", pg_name], check=True)
            print(f"PostgreSQL running on port {POSTGRES_PORT}")
            # 跳过创建，直接处理 Redis
    if not docker_container_exists(pg_name):
        print(f"Creating PostgreSQL container on port {POSTGRES_PORT}...")
        subprocess.run([
            "docker", "run", "-d",
            "--name", pg_name,
            "-e", f"POSTGRES_USER=postgres",
            "-e", f"POSTGRES_PASSWORD=postgres",
            "-e", f"POSTGRES_DB={PROJECT_NAME.replace('-', '_')}",
            "-p", f"{POSTGRES_PORT}:5432",
            "postgres:17-alpine"
        ], check=True)

    # 启动 Redis（复用已有容器，加 --clean 参数重建）
    if docker_container_exists(redis_name):
        if "--clean" in sys.argv:
            print(f"Removing existing Redis container...")
            docker_rm(redis_name)
        else:
            print(f"Starting existing Redis container...")
            subprocess.run(["docker", "start", redis_name], check=True)
            print(f"Redis running on port {REDIS_PORT}")
    if not docker_container_exists(redis_name):
        print(f"Creating Redis container on port {REDIS_PORT}...")
        subprocess.run([
            "docker", "run", "-d",
            "--name", redis_name,
            "-p", f"{REDIS_PORT}:6379",
            "redis:7-alpine"
        ], check=True)

    print("Services started. Run in separate terminals:")
    print(f"  Backend:  cd {project_root}/backend && cargo run")
    print(f"  Frontend: cd {project_root}/frontend && npm run dev")
    print(f"\nAPI will be available at http://localhost:{BACKEND_PORT}")
    print(f"Frontend will be available at http://localhost:{FRONTEND_PORT}")

if __name__ == "__main__":
    main()
```

---

## 生成时的注意事项

1. `{{PROJECT_NAME}}` 替换为实际项目名（kebab-case）
2. dev-start.py 中 PROJECT_NAME 变量也需替换
3. 如果 Docker 不可用，提示用户需自行安装 PostgreSQL 和 Redis
