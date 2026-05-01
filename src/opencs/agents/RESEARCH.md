# Agent Core · OSS 调研

## 目标
实现 Orchestrator（意图分类 + Worker 委派）和 CS Reply Worker（LLM 生成回复 → 提交 ActionPlan），提供 `LLMClient` 可注入接口使 CI 不依赖真实 API。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| [LiteLLM](https://github.com/BerriAI/litellm) | MIT | 2026-04 | 15k | ~12MB | ✅ 复用 | 多 provider 统一接口；§6.6 已锁定 |
| [LangGraph](https://github.com/langchain-ai/langgraph) | MIT | 2026-04 | 10k | ~8MB | ⚠️ 借抽象 | StateGraph + checkpoint 思路优秀；但直接依赖绑定 LangChain 生态，MVP 封装成本高 |
| [Pydantic AI](https://github.com/pydantic/pydantic-ai) | MIT | 2026-03 | 8k | ~2MB | ⚠️ 考察 | Agent 运行时轻量；但与 OpenCS ActionPlan/Harness 模型不完全契合 |
| [CrewAI](https://github.com/crewAIInc/crewAI) | MIT | 2026-04 | 24k | ~6MB | ❌ | 多 agent 协作模型与 OpenCS Orchestrator+Worker 模型不一致；引入会造成抽象冲突 |

## 决策
- **复用**：`litellm @ ^1.51` —— 仅用作 LLM API 调用层；通过 `LLMClient` Protocol 注入，CI 走 `FakeLLMClient`
- **借抽象**：LangGraph StateGraph checkpoint 思路 → Orchestrator 的 intent→delegate 状态机按此思路手写（< 150 行）
- **自建**：`Orchestrator`、`BaseWorker`、`CSReplyWorker`、`ApprovalRouterWorker` —— 业务语义高度定制，无合身 OSS

## 集成边界
- `litellm` 仅在 `LiteLLMClient` 类内调用；`BaseWorker` 只持有 `LLMClient` Protocol
- `CSReplyWorker` 产出 `ActionPlan`，不持有 `ChannelAdapter` 引用
- `Orchestrator` 是唯一持有 Harness 引用的 agent 层组件

## 升级与停更预案
- LiteLLM 若停更：`LiteLLMClient` 是唯一修改点（~50 行）；直接换 `httpx` + OpenAI-compatible endpoint
- 切 LangGraph：届时把 `orchestrator.py` 的状态机迁移到 `StateGraph`；Worker 接口不变
