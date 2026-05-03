# web-ui · OSS 调研

## 目标
OpenCS Admin Web UI：HITL 审批、审计日志、Replay 触发、CRM 配置向导。单租户、低并发、自托管。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| Next.js 14 (App Router) | MIT | 2026-04 | 125k | — | ✅ | spec §6.6 锁定；team 熟悉 |
| Remix v2 | MIT | 2026-03 | 30k | — | ❌ | team 未使用；无明显优势 |
| SvelteKit | MIT | 2026-04 | 18k | — | ❌ | 语言切换成本 |

**UI 库**: shadcn/ui（非依赖，复制粘贴组件；MIT）— 与 spec §6.6 一致
**数据获取**: TanStack Query v5（spec 锁定）
**表单**: react-hook-form + zod（事实标准）

## 决策
- **复用**: Next.js 14 + shadcn/ui + TanStack Query + react-hook-form/zod
- 无自建

## 集成边界
- 所有后端通过 `/api/*` rewrite 代理到 `OPENCS_API_BASE`（默认 `http://opencs-api:8000/admin`）
- 类型通过手写 `src/lib/types.ts` 映射 pydantic schemas（Phase 7c 可加 openapi-ts 自动生成）

## 升级与停更预案
- 跟踪 Next.js major releases
- shadcn/ui 是 copy-in，无停更风险
