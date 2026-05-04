# OpenCS Admin Web UI

OpenCS 管理控制台 — 基于 Next.js 14 App Router 构建，消费 `/admin/*` REST API。

## 技术栈

| 库 | 版本 | 用途 |
|----|------|------|
| Next.js | 14.2 | App Router + standalone 输出 |
| TanStack Query | v5 | 数据获取、缓存、失效 |
| shadcn-style UI | copy-in | Button、Card、Table、Dialog 等原语 |
| Tailwind CSS | 3.4 | 样式 |
| react-hook-form + zod | 7 / 3 | 表单校验 |
| Vitest + RTL | 2 / 16 | 组件测试 |

## 页面

| 路由 | 功能 |
|------|------|
| `/` | Dashboard：待审批数、今日审批/拒绝统计，10s 自动刷新 |
| `/proposals` | HITL 审批列表，支持 status / dimension 过滤 |
| `/proposals/[id]` | 提案详情：payload、replay verdict、Approve / Reject 对话框 |
| `/audit-log` | 分页审计日志，支持 actor 过滤 |
| `/replays` | 配置 + 触发 Replay（conversation ID、mode、prompt override），查看 verdict |
| `/crm` | 四步向导：Base URL → OpenAPI Schema → Validate → 选择 Operations → Save |

## 开发

**前置：** Node.js 20+，运行中的 `opencs-api`（端口 8000）

```bash
cd web-ui
npm install
OPENCS_API_BASE=http://localhost:8000 npm run dev
# → http://localhost:3000
```

所有 `/api/admin/*` 请求由 Next.js rewrite 代理到 `OPENCS_API_BASE/admin/*`，无需手动配置 CORS。

## 测试与构建

```bash
npm test           # Vitest 组件测试（一次性运行）
npm run test:watch # Vitest 监听模式
npm run typecheck  # tsc --noEmit（TypeScript 类型检查）
npm run build      # Next.js 生产构建（同时作为 smoke test）
npm run lint       # ESLint
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENCS_API_BASE` | `http://opencs-api:8000` | 后端地址（Docker Compose 内默认） |

本地开发时通过 `OPENCS_API_BASE=http://localhost:8000 npm run dev` 覆盖。

## Langfuse Trace 深链接

在浏览器 DevTools → Application → Local Storage 中设置：

```
langfuse_host = http://localhost:3001
```

设置后，`/proposals/[id]` 页面会将 `trace_id` 渲染为可点击的 Langfuse 链接。

## Docker 构建

Web UI 使用三阶段构建（`Dockerfile.web`）：

1. **deps** — `npm ci` 安装依赖
2. **builder** — `npm run build` 生成 Next.js standalone 输出
3. **runner** — node:20-alpine，非 root 用户运行，仅包含 standalone 产物

standalone 模式下无需完整 node_modules，镜像体积显著减小。
