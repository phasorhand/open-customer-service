# evolution · OSS 调研

## 目标
构建 Dual-Track Evolution 层：所有对 Skill 文件、L2 Memory、ToolRegistry 的变更都走
Proposal → EvolutionGate（自动晋升或 HITL 人审）→ Handler 应用。ShadowRunner 在晋升前
用 ReplayEngine 做 WhatIf 验证，阻止 verdict=INCONCLUSIVE 的 proposal 进门控。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| LangGraph | MIT | 2026-04 | 9.1k | ~8MB | ❌ | spec §6.6 明确"借抽象，不直接依赖"；StateGraph checkpoint 概念有参考价值，但直接引入会给 Evolution 状态机带来不必要的 LangChain 耦合 |
| Temporal (Python SDK) | MIT | 2026-04 | 3.2k | ~45MB | ❌ | 体量超载否决：依赖树 >50MB，引入独立 Temporal Server；MVP 中 Evolution 是进程内同步流水线，不需要分布式工作流编排 |
| arq | MIT | 2025-11 | 2.8k | ~0.4MB | ⚠️ | spec §6.6 已锁定用于后台任务队列；MVP Evolution 走进程内同步（不需要 Redis 队列）；v1 引入 arq 做异步 Proposal 消费 |
| prefect | Apache-2.0 | 2026-04 | 16k | ~120MB | ❌ | 体量超载否决 |
| pydantic v2 | MIT | 2026-04 | 21k | ~2MB | ✅ | 已是项目依赖；Proposal 数据模型直接用 BaseModel + frozen=True；零额外依赖 |

## 决策
- **自建**：EvolutionGate + ProposalStore + 三维 Handler + ShadowRunner + EvolutionHITLQueue
  - 理由：Dual-Track Evolution（自动晋升 vs HITL 人审，含维度策略 + ShadowRunner 阻断）是 OpenCS 核心差异化——spec §6.6 C 栏明确列为"必须自建"
  - LangGraph 借抽象（StateGraph 分支模式），但不引入依赖；进程内流水线足够 MVP
  - OSS 等价物保留：v1 引入 `arq` 做异步 Proposal 队列；v1+ 评估 LangGraph 做复杂多步 Evolution 工作流
- **复用**：`pydantic v2`（Proposal 数据模型）、`SQLite`（ProposalStore，延续 AuditLog/L0/L2 的现有模式）、`ReplayEngine`（Phase 5，ShadowRunner 的执行后端）

## 集成边界
- `EvolutionGate` 是唯一对外决策入口：`evaluate(proposal) -> GateDecision`
- `ProposalStore` 只做持久化，不含决策逻辑
- `SkillProposalHandler` / `MemoryProposalHandler` / `CRMToolProposalHandler` 只接收已通过 Gate 的 proposal；Gate 不负责应用
- `ShadowRunner` 包装 `ReplayEngine`，不直接写任何状态
- `EvolutionHITLQueue` 持有 proposal_id → EvolutionHITLItem 映射；审批后调用方负责触发 Handler.apply()

## 升级与停更预案
- pydantic v2：主流、活跃；如 API 破坏性变更，`Proposal` 类内部 migration 即可
- SQLite ProposalStore：无外部依赖风险；v1 可平替为 Postgres（SQLAlchemy 方言中性）
- ShadowRunner → ReplayEngine：自建模块，无外部停更风险
