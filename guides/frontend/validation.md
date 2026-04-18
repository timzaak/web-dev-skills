# 编译验证步骤

⚠️ **CRITICAL**: 在标记任务为"完成"之前，**必须**执行以下验证。

## 验证清单

### 1. 类型检查（MANDATORY）

```bash
cd frontend && npm run type-check
# 或
cd frontend && npx tsc --noEmit
```

**验收标准**：
- ✅ 类型检查通过（**0 errors**）
- ⚠️ 警告可以接受，但必须记录

**如果类型检查失败**：
1. 分析类型错误（隐式 any、类型不匹配、导入错误等）
2. **立即修复类型错误**
3. 重新验证：`npm run type-check`
4. 最多重试 3 次
5. **仍然失败**：❌ 不能标记任务为"完成"

**重要**：
- 类型错误必须在完成前修复
- 不能将"类型检查有错误"的任务标记为"完成"
- 这是任务完成的**必要条件**，不是可选步骤

### 2. 构建验证（MANDATORY）

```bash
cd frontend && npm run build
```

**验收标准**：
- ✅ 构建成功
- ✅ 所有模块正确打包到 `dist/`

如果构建失败：
1. 分析构建错误（依赖问题、导入错误等）
2. **立即修复构建错误**
3. 重新验证：`npm run build`
4. 最多重试 3 次

### 3. 代码质量检查（可选但推荐）

```bash
cd frontend && npm run lint
# 或
cd frontend && npx eslint . --ext .ts,.tsx
```

## 任务完成定义

**只有在以下所有条件满足时，才能标记任务为"完成"**：
- ✅ 类型检查通过（**0 errors**）
- ✅ 构建成功
- ✅ 无运行时错误

**如果任何验证失败**：
- ❌ **不能**标记任务为"完成"
- 🔄 **必须**修复并重新验证
- 📝 在完成报告中记录修复过程

## 常见类型错误模式


### 1. 导入错误

查看库的类型定义确认正确的导入方式：

```typescript
// ✅ 正确：默认导入
import OTPInput from 'react-otp-input'

// ❌ 错误：命名导入（该库不支持）
import { OtpInput } from 'react-otp-input'
```

### 2. Props 类型

为 renderInput 等回调参数添加显式类型：

```typescript
// ✅ 正确：显式类型
renderInput={(props: React.ComponentProps<'input'>) => (
  <input {...props} />
)}

// ❌ 错误：隐式 any
renderInput={(props) => <input {...props} />}
```

### 3. 依赖安装

新依赖添加后运行 `npm install`：

```bash
npm install <package-name>
```

### 4. @hey-api/openapi-ts 生成的类型

确保 API 请求/响应与后端一致：

```typescript
// ✅ 正确：使用 @hey-api/openapi-ts 生成的类型
import { createUser } from '@/lib/api-generated'

const response = await createUser({
  body: userData
})

// ❌ 错误：手动定义类型（可能与后端不一致）
interface CreateUserRequest {
  email: string
  // ...
}
```

### 5. 表单类型安全

```typescript
// ✅ 使用 useAppForm（所有表单）
import { useAppForm } from '@/components/ui/tanstack-form'

const form = useAppForm({
  schema: createUserSchema,
  defaultValues: { email: '', password: '' },
})

// ✅ 类型安全提交（onSubmit 回调中自动处理）
onSubmit: async ({ value }) => {
  await mutate(value)
}

// ❌ 禁止 any 或不安全断言
// export function useAppForm({ schema, ...props }: any)
// await mutate(values as CreateUserFormData)

// ❌ 禁止使用 useForm（项目统一规范）
// const form = useForm({ ... })
```

**检查**:
```bash
# 检查是否使用 useAppForm
Grep: "useAppForm" in frontend/src/components/**/*form*.tsx

# 检查类型安全
Grep: "any" in frontend/src/components/**/*form*.tsx
Grep: "as.*FormData" in frontend/src/components/**/*form*.tsx
Grep: "getFieldErrorMessage" in frontend/src/components/**/*form*.tsx

# 检查是否使用 onSubmit 回调
Grep: "onSubmit:" in frontend/src/components/**/*form*.tsx

# 检查是否使用 form.handleSubmit()
Grep: "form\.handleSubmit\(\)" in frontend/src/components/**/*form*.tsx

# 检查是否正确使用 canSubmit（仅在 Subscribe 中允许）
Grep: "form\.state\.canSubmit" in frontend/src/components/**/*form*.tsx | grep -v "Subscribe"
```

**标准**: 零 `any`、零不安全断言、使用 `useAppForm`、使用 `getFieldErrorMessage` 和 `onSubmit`/`form.handleSubmit()`
