# 输出文件清单

`/t-init` 完成后必须确认以下文件存在。用于 Step 1 创建目录结构和 Step 8 验证（读取时机：创建目录或执行收尾验证时）。

**后端（必须）：**
- [ ] `backend/Cargo.toml`
- [ ] `backend/.cargo/config.toml`
- [ ] `backend/.config/nextest.toml`
- [ ] `backend/core/Cargo.toml` + `src/lib.rs` + `src/config.rs` + `src/domain/health.rs` + `src/infrastructure/redis.rs`
- [ ] `backend/api/Cargo.toml` + `src/lib.rs` + `src/config.rs` + `src/application/http/*.rs`
- [ ] `backend/app/Cargo.toml` + `src/main.rs`
- [ ] `backend/config.example.toml`
- [ ] `backend/migrations/00001_init.sql`

**前端（必须）：**
- [ ] `frontend/package.json`
- [ ] `frontend/tsconfig.json`
- [ ] `frontend/vite.config.ts`
- [ ] `frontend/openapi-ts.config.ts`
- [ ] `frontend/index.html`
- [ ] `frontend/src/main.tsx`
- [ ] `frontend/src/styles.css`
- [ ] `frontend/src/routes/__root.tsx`
- [ ] `frontend/src/routes/index.tsx`
- [ ] `frontend/src/components/ui/sonner.tsx`（由 shadcn CLI 生成）
- [ ] `frontend/src/lib/api-client.ts`

**脚本和文档：**
- [ ] `scripts/backend-test.py`
- [ ] `scripts/test-start.py`
- [ ] `scripts/test-stop.py`
- [ ] `scripts/web-demo-test-runner.py`
- [ ] `scripts/web-demo-run-all.py`
- [ ] `scripts/demo-start.py`
- [ ] `scripts/demo-stop.py`
- [ ] `scripts/debug-test.py`
- [ ] `scripts/cleanup-demo.py`
- [ ] `scripts/cleanup-test-logs.py`
- [ ] `scripts/web-demo-failure-summary.py`
- [ ] `scripts/lib/*.py`
- [ ] `README.md`

**AI 辅助配置（必须）：**
- [ ] `AGENTS.md`
- [ ] `CLAUDE.md`

**Demo E2E 测试（必须）：**
- [ ] `demo/package.json`
- [ ] `demo/tsconfig.json`
- [ ] `demo/playwright.config.ts`
- [ ] `demo/eslint.config.js`
- [ ] `demo/.gitignore`
- [ ] `demo/e2e/smoke.e2e.ts`（冒烟测试，不依赖后端）
- [ ] `demo/e2e/demo-basic.e2e.ts`
- [ ] `demo/e2e/fixtures/demo-auth.fixtures.ts`
- [ ] `demo/e2e/fixtures/test-data.ts`
- [ ] `demo/e2e/helpers/auth.ts`
- [ ] `demo/e2e/helpers/environment-setup.ts`
- [ ] `demo/e2e/pages/base-page.ts`
- [ ] `demo/e2e/pages/login-page.ts`
- [ ] `demo/e2e/selectors.ts`
