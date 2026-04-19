# 编译验证步骤

⚠️ **CRITICAL**: 在标记任务为"完成"之前，**必须**执行以下验证。

## 验证清单

### 1. 编译验证（MANDATORY）

```bash
cd backend && cargo check --package <api-package>
```

**验收标准**：
- ✅ 编译成功（**0 errors**）
- ⚠️ 警告可以接受，但必须记录

**如果编译失败**：
1. 分析错误原因（import 错误、类型错误、trait 冲突等）
2. **立即修复编译错误**
3. 重新验证：`cargo check --package <api-package>`
4. 最多重试 3 次
5. **仍然失败**：❌ 不能标记任务为"完成"

**重要**：
- 编译错误必须在完成前修复
- 不能将"编译有错误"的任务标记为"完成"
- 这是任务完成的**必要条件**，不是可选步骤
- `<api-package>` 应替换为目标仓库实际对外 API crate/package 名称；优先从 `backend/` 下的 `Cargo.toml` 或现有脚本确认

### 2. 最终收口（backend accept 后必须执行）

```bash
/simplify
cd backend && cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features
cd backend && cargo fmt --all
cd backend && uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py
```

规则：
- 这一步对应 `/t-backend-finalize [feature]`。
- 这里的 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py` 是全量测试，只属于 finalize，不属于 `backend-accept` 的默认步骤。
- 同一 feature 再次执行时，默认从失败步骤恢复，无需额外参数。

### 3. 格式化检查（可选但推荐）

```bash
cd backend && cargo fmt --check
```

如果格式不正确，运行：
```bash
cd backend && cargo fmt
```

### 4. 快速测试（可选但推荐）

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- --package <core-package> --lib
```

## 任务完成定义

**只有在以下所有条件满足时，才能标记任务为"完成"**：
- ✅ 编译成功（**0 errors**）
- ✅ 代码格式正确（或已格式化）
- ✅ 核心功能测试通过（如果有相关测试）

**如果任何验证失败**：
- ❌ **不能**标记任务为"完成"
- 🔄 **必须**修复并重新验证
- 📝 在完成报告中记录修复过程

## 常见编译错误模式


1. **Import 错误**：正确导入 `axum::extract::{Path, State, Extension}`
2. **Handler 签名**：参考现有 handler（如 `login.rs`）的正确写法
3. **UUID 生成**：使用 `Uuid::now_v7()` 而非 `Uuid::new_v4()`
4. **闭包类型**：`.map_err()` 需要闭包，不是直接传值
5. **Trait 导入**：确保 repository trait 已导入

## 典型错误处理

### Import 错误示例

```rust
// ❌ 错误：未导入 Path
async fn get_user(id: Uuid) -> Result<Json<User>> {
    // ...
}

// ✅ 正确：导入 Path
use axum::extract::{Path, State};
use uuid::Uuid;

async fn get_user(Path(id): Path<Uuid>) -> Result<Json<User>> {
    // ...
}
```

### Handler 签名示例

```rust
// ❌ 错误：缺少 State 提取
async fn create_user(
    Json(payload): Json<CreateUserRequest>,
) -> Result<Json<User>> {
    // ...
}

// ✅ 正确：包含 State 和 Path
async fn create_user(
    State(app_state): State<AppState>,
    Json(payload): Json<CreateUserRequest>,
) -> Result<Json<User>> {
    // ...
}
```

### UUID 生成示例

```rust
// ❌ 错误：使用 v4
let id = Uuid::new_v4();

// ✅ 正确：使用 v7
let id = Uuid::now_v7();
```

### 错误处理示例

```rust
// ❌ 错误：使用 unwrap
let user = user_service.find_by_id(id).unwrap()?;

// ✅ 正确：使用 ? 传播
let user = user_service.find_by_id(id)?;

// ❌ 错误：map_err 需要闭包
.map_err(ServiceError::NotFound)

// ✅ 正确：使用闭包
.map_err(|_| ServiceError::NotFound(id))?
```
