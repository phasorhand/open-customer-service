# tools · OSS 调研

## 目标
提供 Tool Protocol 抽象 + APITool 实现，让 Worker 可以产出指向任意 HTTP API 的 ActionPlan，Orchestrator 通过 ToolExecutor 安全执行。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| httpx (HTTP client) | BSD-3 | 2026-04 | 13.5k | ~2MB | ✅ | 已在 pyproject.toml；异步原生；FastAPI 官方推荐 |
| langchain tools | MIT | 2026-04 | 95k | >100MB | ❌ | 体量超载：依赖树 >100MB；核心 API 与 OpenCS ActionPlan 抽象冲突，封装成本 > 自建 |
| openai function calling SDK | MIT | 2026-04 | — | — | ❌ | 绑定 OpenAI API；与 LiteLLM 抽象冲突；不适用 |

## 决策
- **HTTP 客户端**：复用 `httpx @ >=0.27`（已锁定，见 §6.6 A 类）
- **Tool 协议 + ToolRegistry + APITool + ToolExecutor**：自建
  - 理由：langchain tools 体量否决（依赖树 >100MB）；openai SDK 绑定否决；OpenCS ActionPlan→ToolExecutor 的信任边界（HarnessToken 验证）是 OpenCS 核心安全约定，没有 OSS 等价物
  - OSS 等价物保留为 `langchain-core tools` 以备 v1 切换（如需生态集成）

## 集成边界
- `Tool` Protocol：`describe() / call(args, token) / dry_run(args) / health_check()`
- `ToolRegistry`：仅 `register / get / list_tools`，不暴露给 Worker（Worker 只写 tool_id 字符串）
- `APITool`：透传 httpx response；不对 payload 做业务解析
- `ToolExecutor`：token 验证在此层；不感知 Memory / Channel

## 升级与停更预案
- httpx：跟随 FastAPI 官方 pinned 版本；停更则换 aiohttp（接口相似，切换成本低）
- 自建模块：无停更风险
