# 后端文件模板

本文件包含后端所有需要生成的文件内容模板。
占位符：`{{PROJECT_NAME}}` (kebab-case), `{{PROJECT_NAME_PASCAL}}` (PascalCase), `{{PROJECT_NAME_SNAKE}}` (snake_case)

---

## 1. backend/Cargo.toml (Workspace Root)

```toml
[workspace]
resolver = "2"
members = [
    "domain-core",
    "api",
    "app",
]

[workspace.package]
version = "0.1.0"
edition = "2021"
license = "MIT"

[workspace.dependencies]
# Async runtime
tokio = { version = "1", features = ["macros", "rt-multi-thread", "signal"] }

# Web framework
axum = { version = "0.8", features = ["macros"] }
tower = { version = "0.5" }
tower-http = { version = "0.6", features = ["cors", "trace", "fs"] }

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Database
sea-orm = { version = "1.1", features = ["sqlx-postgres", "runtime-tokio-rustls", "macros", "with-uuid", "with-chrono"] }
sqlx = { version = "0.8", features = ["runtime-tokio-rustls", "any", "postgres", "uuid", "migrate"] }

# Time & ID
chrono = { version = "0.4", features = ["serde"] }
uuid = { version = "1", features = ["v7", "serde"] }

# Error handling
anyhow = "1.0"
thiserror = "2.0"

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# Configuration
toml = "0.8"
clap = { version = "4", features = ["derive", "env"] }
dotenv = "0.15"

# Redis
redis = { version = "0.27", features = ["connection-manager", "tokio-comp", "aio"] }
```

> **注意**：依赖版本应根据 Context7 查询结果更新。上述版本是基线参考。

---

## 2. backend/domain-core/Cargo.toml

```toml
[package]
name = "domain-core"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
# Workspace dependencies
tokio = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
anyhow = { workspace = true }
thiserror = { workspace = true }
tracing = { workspace = true }

# API Documentation
utoipa = { version = "5", features = ["chrono", "uuid"] }

# Database
sea-orm = { workspace = true }
sqlx = { workspace = true }

# Time & ID
chrono = { workspace = true }
uuid = { workspace = true }

# Redis
redis = { workspace = true }

# Configuration
toml = { workspace = true }
```

---

## 3. backend/domain-core/src/lib.rs

```rust
pub mod config;
pub mod domain;
pub mod infrastructure;

pub use config::{AppConfig, DatabaseConfig, RedisConfig, ServerConfig};
pub use domain::health::HealthStatus;
pub use infrastructure::redis::{ManagerConfig, RedisConnectionManager};
```

---

## 4. backend/domain-core/src/config.rs

```rust
use serde::{Deserialize, Serialize};
use std::path::Path;

/// 应用配置
///
/// 从 TOML 配置文件加载，包含服务器、数据库和 Redis 三个部分的配置。
/// 配置文件示例见 config.example.toml。
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub server: ServerConfig,
    pub database: DatabaseConfig,
    pub redis: RedisConfig,
}

impl AppConfig {
    /// 从 TOML 文件加载配置
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self, Box<dyn std::error::Error>> {
        let content = std::fs::read_to_string(path)?;
        let config: AppConfig = toml::from_str(&content)?;
        Ok(config)
    }
}

/// 服务器配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    /// 监听地址，如 "0.0.0.0:8080"
    pub bind_address: String,
    /// 日志级别：trace, debug, info, warn, error
    pub log_level: String,
    /// 运行环境：development, test, production
    pub app_env: String,
    /// 前端静态文件目录（生产模式使用）
    pub static_dir: String,
    /// 是否启用 OpenAPI/Swagger 文档
    /// 设为 true 后可访问 /swagger 查看 API 文档
    pub enable_openapi: bool,
}

/// 数据库配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    /// PostgreSQL 连接字符串
    pub url: String,
    /// 最大连接数
    pub max_connections: u32,
    /// 获取连接超时（秒）
    pub acquire_timeout_secs: u64,
    /// 空闲连接超时（秒）
    pub idle_timeout_secs: u64,
    /// 连接最大生命周期（秒）
    pub max_lifetime_secs: u64,
    /// 连接超时（秒）
    pub connect_timeout_secs: u64,
}

/// Redis 配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RedisConfig {
    /// Redis 连接字符串，如 "redis://127.0.0.1:6379"
    pub url: String,
}
```

---

## 5. backend/domain-core/src/domain/health.rs

```rust
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

/// 健康检查状态
///
/// 用于 GET /health 接口返回，包含各组件的连接状态。
#[derive(Debug, Clone, Serialize, Deserialize, ToSchema)]
pub struct HealthStatus {
    pub status: String,
    pub database: String,
    pub redis: String,
}

impl HealthStatus {
    pub fn new() -> Self {
        Self {
            status: "healthy".to_string(),
            database: "unknown".to_string(),
            redis: "unknown".to_string(),
        }
    }

    pub fn with_database(mut self, status: &str) -> Self {
        self.database = status.to_string();
        self
    }

    pub fn with_redis(mut self, status: &str) -> Self {
        self.redis = status.to_string();
        self
    }

    pub fn is_healthy(&self) -> bool {
        self.status == "healthy"
            && self.database == "connected"
            && self.redis == "connected"
    }
}

impl Default for HealthStatus {
    fn default() -> Self {
        Self::new()
    }
}
```

---

## 6. backend/domain-core/src/infrastructure/redis.rs

```rust
use redis::aio::ConnectionManager;
use serde::{Deserialize, Serialize};

/// Redis 连接管理器配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManagerConfig {
    pub url: String,
    pub default_db: u8,
    pub test_mode: bool,
    pub test_db: u8,
}

/// Redis 连接管理器
///
/// 封装 redis::aio::ConnectionManager，提供健康检查和连接克隆功能。
#[derive(Clone)]
pub struct RedisConnectionManager {
    manager: ConnectionManager,
    #[allow(dead_code)]
    config: ManagerConfig,
}

impl RedisConnectionManager {
    /// 创建新的 Redis 连接管理器
    pub async fn new(config: ManagerConfig) -> Result<Self, redis::RedisError> {
        let client = redis::Client::open(config.url.clone())?;
        let manager = ConnectionManager::new(client).await?;
        Ok(Self { manager, config })
    }

    /// 健康检查 — 发送 PING 命令
    pub async fn health_check(&self) -> Result<(), redis::RedisError> {
        let mut conn = self.manager.clone();
        let _: String = redis::cmd("PING").query_async(&mut conn).await?;
        Ok(())
    }

    /// 获取底层连接管理器的克隆
    pub fn clone_manager(&self) -> ConnectionManager {
        self.manager.clone()
    }
}
```

---

## 7. backend/api/Cargo.toml

```toml
[package]
name = "api"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
domain-core = { path = "../domain-core" }

# Workspace dependencies
tokio = { workspace = true }
axum = { workspace = true }
tower = { workspace = true }
tower-http = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
anyhow = { workspace = true }
tracing = { workspace = true }
tracing-subscriber = { workspace = true }
sea-orm = { workspace = true }
sqlx = { workspace = true }

# Configuration
clap = { workspace = true }
toml = { workspace = true }
dotenv = { workspace = true }

# API Documentation — utoipa 自动生成 OpenAPI 文档
utoipa = { version = "5", features = ["axum_extras", "uuid", "chrono", "openapi_extensions"] }
utoipa-swagger-ui = { version = "9", features = ["axum", "vendored"] }
```

---

## 8. backend/api/src/lib.rs

```rust
pub mod application;
pub mod config;

pub use application::http::{create_api_routes, ApiDoc};
pub use application::http::AppState;
pub use config::ApiConfig;

use anyhow::Result;
use std::sync::Arc;
use utoipa::OpenApi;

/// 导出 OpenAPI 规范到文件
///
/// 通过命令行参数 `--export-openapi <path>` 触发，
/// 将 OpenAPI JSON 写入指定路径，供前端生成 TypeScript 客户端。
pub fn export_openapi(output_path: &str) -> Result<()> {
    let openapi = ApiDoc::openapi();
    let json = serde_json::to_string_pretty(&openapi)?;
    std::fs::write(output_path, json)?;
    println!("OpenAPI spec exported to {}", output_path);
    Ok(())
}
```

---

## 9. backend/api/src/config.rs

```rust
use domain_core::AppConfig;

/// API 层配置
///
/// 直接复用 domain-core 的 AppConfig。
/// 如需扩展 API 层特有的配置项，可在此添加。
pub type ApiConfig = AppConfig;
```

---

## 10. backend/api/src/application/http/mod.rs

```rust
pub mod handlers;
pub mod openapi;
pub mod routes;
pub mod state;

pub use openapi::ApiDoc;
pub use routes::create_api_routes;
pub use state::AppState;
```

---

## 11. backend/api/src/application/http/state.rs

```rust
use domain_core::infrastructure::redis::RedisConnectionManager;
use sea_orm::DatabaseConnection;
use sqlx::PgPool;
use std::sync::Arc;

/// 应用共享状态
///
/// 所有路由处理函数通过 Axum 的 State 提取器访问此结构体。
/// 使用 Arc 包装以实现高效的共享所有权。
#[derive(Clone)]
pub struct AppState {
    /// SQLx 连接池 — 用于原生 SQL 查询和迁移
    pub pool: PgPool,
    /// Sea-ORM 数据库连接 — 用于 ORM 操作
    pub db: Arc<DatabaseConnection>,
    /// Redis 连接管理器 — 用于缓存和会话存储
    pub redis_manager: RedisConnectionManager,
    /// 前端静态文件目录路径
    pub static_dir: String,
    /// 是否启用 OpenAPI/Swagger 文档
    pub enable_openapi: bool,
}
```

---

## 12. backend/api/src/application/http/openapi.rs

```rust
use utoipa::OpenApi;
use utoipa::openapi::security::{HttpAuthScheme, HttpBuilder, SecurityScheme};

/// OpenAPI 文档定义
///
/// utoipa 会根据此 derive 宏自动生成 OpenAPI 3.0 规范。
/// 新增路由后，需要在此处的 paths() 中注册对应的处理函数，
/// 新增数据结构后，需要在 components(schemas()) 中注册。
///
/// 访问方式：
/// - enable_openapi = true 时，访问 /swagger 查看 Swagger UI
/// - enable_openapi = false 时，/swagger 返回 404
#[derive(OpenApi)]
#[openapi(
    info(
        title = "{{PROJECT_NAME_PASCAL}} API",
        version = "0.1.0",
        description = "{{PROJECT_NAME_PASCAL}} API Documentation",
        license(name = "MIT")
    ),
    paths(
        crate::application::http::handlers::health_check,
    ),
    components(
        schemas(domain_core::domain::health::HealthStatus)
    ),
    tags(
        (name = "health", description = "Health check endpoints")
    ),
    modifiers(&SecurityAddon)
)]
pub struct ApiDoc;

/// 安全方案附加组件
///
/// 在 OpenAPI 文档中注册 Bearer Token (JWT) 认证方案。
/// 当有需要认证的接口时，在 utoipa::path 注解中添加
/// security(("bearer_auth" = [])) 即可。
struct SecurityAddon;

impl utoipa::Modify for SecurityAddon {
    fn modify(&self, openapi: &mut utoipa::openapi::OpenApi) {
        if let Some(components) = openapi.components.as_mut() {
            components.add_security_scheme(
                "bearer_auth",
                SecurityScheme::Http(
                    HttpBuilder::new()
                        .scheme(HttpAuthScheme::Bearer)
                        .bearer_format("JWT")
                        .build(),
                ),
            )
        }
    }
}
```

---

## 13. backend/api/src/application/http/handlers.rs

```rust
use axum::{extract::State, Json};
use domain_core::domain::health::HealthStatus;
use std::sync::Arc;
use utoipa::ToSchema;

use crate::application::http::state::AppState;

/// 健康检查响应
#[derive(ToSchema)]
pub struct HealthResponse {
    status: String,
    database: String,
    redis: String,
}

/// 健康检查接口
///
/// GET /health
/// 返回 API 及其依赖服务（数据库、Redis）的连接状态。
#[utoipa::path(
    get,
    path = "/health",
    tag = "health",
    responses(
        (status = 200, description = "API is healthy", body = HealthStatus),
        (status = 503, description = "API is unhealthy", body = HealthStatus)
    )
)]
pub async fn health_check(
    State(state): State<Arc<AppState>>,
) -> Result<Json<HealthStatus>, axum::http::StatusCode> {
    let db_status = match sqlx::query("SELECT 1")
        .fetch_one(&state.pool)
        .await
    {
        Ok(_) => "connected".to_string(),
        Err(e) => {
            tracing::error!("Database health check failed: {}", e);
            format!("error: {}", e)
        }
    };

    let redis_status = match state.redis_manager.health_check().await {
        Ok(_) => "connected".to_string(),
        Err(e) => {
            tracing::error!("Redis health check failed: {}", e);
            format!("error: {}", e)
        }
    };

    let status = HealthStatus::new()
        .with_database(&db_status)
        .with_redis(&redis_status);

    Ok(Json(status))
}
```

---

## 14. backend/api/src/application/http/routes.rs

```rust
use axum::{Router, routing::get};
use axum::http::StatusCode;
use tower_http::services::{ServeDir, ServeFile};
use crate::application::http::{
    handlers::health_check,
    openapi::ApiDoc,
    state::AppState,
};
use utoipa::OpenApi;

/// 创建 API 路由
///
/// 这是路由注册的入口点。所有 API 路由都在此函数中注册。
///
/// 路由结构：
/// - /health — 健康检查（始终可用）
/// - /swagger — Swagger UI（仅 enable_openapi = true 时可用）
/// - 其他路径 — 代理到前端静态文件
///
/// 添加新路由的模式：
/// 1. 在 handlers.rs 中创建处理函数并添加 #[utoipa::path] 注解
/// 2. 在 openapi.rs 的 paths() 中注册
/// 3. 在此函数中添加 .route("/your-path", get(your_handler))
pub fn create_api_routes(state: std::sync::Arc<AppState>) -> Router {
    let frontend_static_dir = state.static_dir.clone();
    let app = Router::new()
        .route("/health", get(health_check))
        .with_state(state.clone());

    // OpenAPI 开关：根据配置决定是否暴露 Swagger 文档
    let app = if state.enable_openapi {
        let swagger_ui = utoipa_swagger_ui::SwaggerUi::new("/swagger")
            .url("/api-docs/openapi.json", ApiDoc::openapi());
        app.merge(swagger_ui)
    } else {
        // 关闭时返回 404，避免暴露 API 文档
        app.route("/swagger", get(|| async { StatusCode::NOT_FOUND }))
            .route("/swagger/", get(|| async { StatusCode::NOT_FOUND }))
            .route(
                "/api-docs/openapi.json",
                get(|| async { StatusCode::NOT_FOUND }),
            )
    };

    // 前端静态文件服务：未匹配的路径代理到前端 SPA
    app.fallback_service(
        ServeDir::new(&frontend_static_dir)
            .fallback(ServeFile::new(format!("{frontend_static_dir}/index.html"))),
    )
}
```

---

## 15. backend/app/Cargo.toml

```toml
[package]
name = "app"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
domain-core = { path = "../domain-core" }
api = { path = "../api" }

# Workspace dependencies
tokio = { workspace = true }
anyhow = { workspace = true }
tracing = { workspace = true }
tracing-subscriber = { workspace = true }
clap = { workspace = true }
dotenv = { workspace = true }
sqlx = { workspace = true }
sea-orm = { workspace = true }
axum = { workspace = true }
```

---

## 16. backend/app/src/main.rs

```rust
use anyhow::Result;
use clap::Parser;
use std::env;
use tracing_subscriber::prelude::*;

/// {{PROJECT_NAME_PASCAL}} Backend Application
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// 配置文件路径
    #[arg(short, long, default_value = "config.toml")]
    config: String,

    /// 导出 OpenAPI 规范到文件
    /// 用法：cargo run --export-openapi ../frontend/api.json
    #[arg(long, value_name = "FILE")]
    export_openapi: Option<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    // 处理 OpenAPI 导出模式
    // 运行 cargo run --export-openapi <path> 只导出 API 规范，不启动服务器
    if let Some(output_path) = args.export_openapi {
        return api::export_openapi(&output_path);
    }

    // 加载配置
    let config_path = env::var("APP_CONFIG").unwrap_or(args.config);
    let config = api::ApiConfig::load(&config_path)
        .map_err(|e| anyhow::anyhow!("Failed to load config from {}: {}", config_path, e))?;

    // 初始化日志
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| config.server.log_level.clone().into()),
        )
        .with(
            tracing_subscriber::fmt::layer()
                .with_ansi(false)
                .with_target(true)
                .with_thread_ids(true)
                .with_level(true),
        )
        .init();

    tracing::info!("Starting {{PROJECT_NAME_PASCAL}} Application");
    tracing::info!("Config loaded from: {}", config_path);
    tracing::info!("Bind address: {}", config.server.bind_address);
    tracing::info!("OpenAPI enabled: {}", config.server.enable_openapi);

    // 创建 sqlx 连接池 — 用于原生查询和数据库迁移
    let pg_pool = sqlx::postgres::PgPoolOptions::new()
        .max_connections(config.database.max_connections)
        .acquire_timeout(std::time::Duration::from_secs(config.database.acquire_timeout_secs))
        .idle_timeout(std::time::Duration::from_secs(config.database.idle_timeout_secs))
        .max_lifetime(std::time::Duration::from_secs(config.database.max_lifetime_secs))
        .connect_timeout(std::time::Duration::from_secs(config.database.connect_timeout_secs))
        .connect(&config.database.url)
        .await?;

    // 运行数据库迁移
    sqlx::migrate!("../migrations")
        .run(&pg_pool)
        .await?;
    tracing::info!("Database migrations completed");

    // 创建 Sea-ORM 数据库连接
    let mut db_opts = sea_orm::ConnectOptions::new(&config.database.url);
    db_opts
        .max_connections(config.database.max_connections)
        .acquire_timeout(std::time::Duration::from_secs(config.database.acquire_timeout_secs))
        .idle_timeout(std::time::Duration::from_secs(config.database.idle_timeout_secs))
        .max_lifetime(std::time::Duration::from_secs(config.database.max_lifetime_secs))
        .connect_timeout(std::time::Duration::from_secs(config.database.connect_timeout_secs));
    let db: sea_orm::DatabaseConnection = sea_orm::Database::connect(db_opts).await?;

    // 连接 Redis
    let redis_config = domain_core::infrastructure::redis::ManagerConfig {
        url: config.redis.url.clone(),
        default_db: 0,
        test_mode: config.server.app_env == "test",
        test_db: 1,
    };
    let redis_manager = domain_core::infrastructure::redis::RedisConnectionManager::new(redis_config)
        .await
        .map_err(|e| anyhow::anyhow!("Failed to create Redis manager: {}", e))?;

    redis_manager
        .health_check()
        .await
        .map_err(|e| anyhow::anyhow!("Redis health check failed: {}", e))?;
    tracing::info!("Connected to Redis");

    // 构建应用状态
    let app_state = std::sync::Arc::new(api::application::http::AppState {
        pool: pg_pool.clone(),
        db: std::sync::Arc::new(db),
        redis_manager,
        static_dir: config.server.static_dir.clone(),
        enable_openapi: config.server.enable_openapi,
    });

    // 创建路由并启动服务器
    let app = api::create_api_routes(app_state);
    let listener = tokio::net::TcpListener::bind(&config.server.bind_address).await?;
    tracing::info!("Server listening on {}", config.server.bind_address);

    axum::serve(listener, app).await?;

    Ok(())
}
```

---

## 17. backend/config.example.toml

```toml
# {{PROJECT_NAME_PASCAL}} Backend Configuration
# 复制此文件为 config.toml 并修改配置值

[server]
# 监听地址
bind_address = "0.0.0.0:8080"
# 日志级别：trace, debug, info, warn, error
log_level = "info"
# 运行环境：development, test, production
app_env = "development"
# 前端静态文件目录（生产环境使用，开发时由 Vite 代理）
static_dir = "../frontend/dist"
# 是否启用 OpenAPI/Swagger 文档
# true → 访问 /swagger 查看 API 文档
# false → /swagger 返回 404
enable_openapi = true

[database]
# PostgreSQL 连接字符串
url = "postgres://postgres:postgres@localhost:5432/{{PROJECT_NAME_SNAKE}}"
# 连接池配置
max_connections = 10
acquire_timeout_secs = 30
idle_timeout_secs = 600
max_lifetime_secs = 1800
connect_timeout_secs = 10

[redis]
# Redis 连接字符串
url = "redis://127.0.0.1:6379"
```

---

## 18. backend/migrations/00001_init.sql

```sql
-- 初始迁移：创建基本表结构
-- 后续根据业务需求在此目录下添加新的迁移文件

-- 示例：如果需要用户表，取消注释以下内容
-- CREATE TABLE IF NOT EXISTS users (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     username VARCHAR(255) NOT NULL UNIQUE,
--     email VARCHAR(255) NOT NULL UNIQUE,
--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
--     updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
-- );
```

---

## 生成时的注意事项

1. 所有 `{{PROJECT_NAME}}` 替换为实际项目名（kebab-case，如 `my-project`）
2. 所有 `{{PROJECT_NAME_PASCAL}}` 替换为 PascalCase（如 `MyProject`）
3. 所有 `{{PROJECT_NAME_SNAKE}}` 替换为 snake_case（如 `my_project`）
4. 依赖版本应根据 Context7 查询结果更新
5. 如果 Axum 版本更新导致 API 变化，调整路由和状态共享代码
6. 确保 `sqlx::migrate!` 宏的路径与实际 migrations 目录匹配
