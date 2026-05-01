# OpenCS —— 开源私域运营 AI 平台 · MVP 架构设计

> **日期**：2026-04-30
> **文档性质**：顶层架构 Spec（MVP 范围）
> **后续**：本 spec 通过后，进入 `writing-plans` 流程拆解实施计划

---

## § 1. 项目定位与命名

**工作代号**：`OpenCS`（Open Customer Service）

**一句话定位**
> 开源、可自托管、以 **Teamily-style Agent Social Brain** 为架构骨架的**私域运营 AI 平台**；MVP 聚焦「企微客服闭环 + CRM 自动对接 + 双轨进化（Self-evolve / HITL）」。

**核心差异化**

| 维度 | Hermes | OpenClaw | OpenHands | OpenCS |
|---|---|---|---|---|
| 主场景 | 个人助理 | 个人助理 + 多通道 | 软件工程 | **私域商业运营** |
| 多 Agent | Subagent 委派 | 单 agent + 插件 | 单 CodeActAgent | **Orchestrator + Worker 社交网络** |
| 工具层 | Toolset / MCP | Plugin / MCP | AgentSkills | **ToolProvider 抽象 + CRM 自动生成** |
| 自进化 | Skill 自创建 | Skill + Dreaming | AgentSkills | **5 维双轨进化（Self-evolve vs HITL）** |
| 部署 | 常驻 server | 本地优先 Gateway | Docker/Cloud | **企业自托管优先，私域合规为先** |

**核心非目标（明确不做）**
- 不自建 CRM 数据模型（只做 CRM 适配层）
- 不替代企微 / 飞书的 IM 能力（作为它们的 agent 消费方）
- MVP 不做多租户 SaaS（单组织自托管优先，多租户 v2）

**MVP 端到端闭环**
> 用户在企微发消息 → agent 理解 → 查 CRM（通过自动生成的 tool）→ 回复用户（高风险动作经 HITL）→ 沉淀这次处理流程为 skill

**关键已决策**
- 控制模式：**Autopilot with Guardrails**
- Agent 架构：**Orchestrator + Worker**（MVP 2 个 worker：CS Reply、Approval Router；CRM Explorer 等推到 v1）
- CRM 对接：**MVP 手工配置 + 只读 API tool**；自动探索（API 优先 + UI 兜底）推到 v1
- Self-evolve 维度：**目标 5 维**（Skill / Memory / Prompt / CRM-Tool / Signal-Loop），**MVP 仅启用前三维**（Skill / Memory / CRM-Tool）；严格区分 Self-evolve / HITL（**Dual-Track Evolution**）
- 技术栈：**Python（FastAPI + Playwright + LiteLLM）+ TypeScript/React 前端**

---

## § 2. 整体架构分层

```
┌───────────────────────────────────────────────────────────────────────┐
│                      § 外部系统接入层（Channel Gateway）               │
│   企微客服接口  │  企微群机器人  │  飞书群  │  WebChat  │  CLI/TUI      │
└──────────┬────────────────────────────────────────────────────────────┘
           │ 统一消息事件（Inbound Message Event）
┌──────────▼────────────────────────────────────────────────────────────┐
│                      § Social Perception 层（感知）                    │
│   多模态解析  │  多轮会话重建  │  多人/多 agent 识别  │  会话状态机     │
└──────────┬────────────────────────────────────────────────────────────┘
           │
┌──────────▼────────────────────────────────────────────────────────────┐
│                     § Social Brain 层（决策/规划）                     │
│   Orchestrator Agent  │  Intent Classification  │  Workflow Planner   │
│   Proactive Scheduler（主动提醒/外呼）                                 │
└──────────┬────────────────────────────────────────────────────────────┘
           │ 任务派发（Delegate / Co-work）
┌──────────▼────────────────────────────────────────────────────────────┐
│                   § Worker Agent 社交网络（执行）                      │
│  ┌──────────────┐ ┌──────────────┐ │ ┌──────────────┐ ┌────────────┐ │
│  │ CS Reply     │ │ Approval     │ │ │ CRM Explorer │ │ Knowledge  │ │
│  │ Agent  [MVP] │ │ Router [MVP] │ │ │ Agent  (v1)  │ │ Agent (v1) │ │
│  └──────┬───────┘ └──────┬───────┘ │ └──────────────┘ └────────────┘ │
└─────────┼────────────────┼─────────┴─────────────────────────────────┘
          │                │
┌─────────▼────────────────▼────────────────────────────────────────────┐
│           § 共享能力层（Skills / Memory / Tools / Harness）            │
│  ┌────────────┐ ┌────────────┐ ┌────────────────┐ ┌────────────────┐ │
│  │ Skill Repo │ │ Memory     │ │ ToolProvider   │ │ Harness /      │ │
│  │ bundled    │ │ L0/L1/L2   │ │ MVP: API only  │ │ ActionGuard    │ │
│  │ +learned v1│ │ 三层模型   │ │ v1: +UI +MCP   │ │ +ExecutionToken│ │
│  └────────────┘ └────────────┘ └────────────────┘ └────────────────┘ │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│               § Evolution 层（双轨进化 Self-evolve / HITL）             │
│   ProposalQueue  │  Shadow Runner  │  Promotion Gate  │  AuditLog     │
│   目标 5 维：Skill / Memory / Prompt&Config / CRM-Tool / Signal-Loop   │
│   **MVP 启用前 3 维**（Skill / Memory / CRM-Tool）                      │
└───────────────────────────────────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────────────────┐
│   § Replay 引擎（核心：What-if 验证 badcase 修复；含 Strict/Partial）   │
│   修复 Proposal 必须附 Replay verdict 才能进 PromotionGate              │
└───────────────────────────────────────────────────────────────────────┘
```

**关键设计原则**

1. **每层只和相邻层通信**
2. **Evolution 层横切所有层**：只观察事件 + 产出 proposal，不直接改运行代码；所有晋升都走 ProposalQueue + PromotionGate
3. **Worker Agent 之间不直连**：必须通过 Orchestrator 或共享 Memory 协作
4. **Harness 是唯一执行入口（Hard Boundary）**：
   - Worker Agent **不能直接调用** `ToolProvider`；只能产出 `ActionPlan { tool_id, args, intent, risk_hint }`
   - `ActionGuard` 接收 `ActionPlan` → 分类（Green/Yellow/Orange/Red）→ 审批 → 签发短期 `ExecutionToken`
   - 运行时凭 `ExecutionToken` 调用 `ToolProvider.call(args, token)`；`ToolProvider` 校验 token 有效性后再执行
   - 这条是**类型系统级别的强制**，不是规约——任何绕过 Harness 的 tool 调用在编译/启动期就应当失败

---

## § 3. 核心模块边界

### 3.1 Channel Gateway
- **职责**：统一接入层，规范化消息为 `InboundMessage` 事件、把 `OutboundAction` 翻译为各平台原生 API 调用
- **核心抽象**：`ChannelAdapter` 基类——所有 IM 平台都是它的子类
- **MVP 支持**：`WecomCustomerServiceAdapter`（企微客服 1-on-1）、`WebChatAdapter`（内部调试）
- **v1**：`FeishuAdapter`、`WecomGroupBotAdapter`
- **v2**：`TelegramAdapter`、`SlackAdapter`、语音通道
- **依赖**：Harness（出站动作必须走 ActionGuard）

#### 3.1.1 ChannelAdapter 基类接口

```python
class ChannelAdapter(ABC):
    """所有 IM 平台子类的统一契约。Gateway 只持有 ChannelAdapter 引用，不感知具体平台。"""

    channel_id: str           # "wecom_cs" / "feishu" / "webchat"
    capabilities: ChannelCapabilities  # 见下

    # —— Inbound：平台原生事件 → 统一 InboundMessage ——
    @abstractmethod
    async def parse_inbound(self, raw_event: dict) -> InboundMessage:
        """回调/webhook payload → 统一 schema。负责解密、签名校验、消息拉取。"""

    # —— Outbound：统一 OutboundAction → 平台原生 API ——
    @abstractmethod
    async def send(self, action: OutboundAction, token: ExecutionToken) -> SendResult:
        """必须校验 ExecutionToken（Harness 签发）才执行。"""

    # —— 生命周期 ——
    @abstractmethod
    async def on_install(self, config: ChannelConfig) -> None: ...
    @abstractmethod
    async def health_check(self) -> HealthStatus: ...

    # —— 可选能力（子类按需实现，由 capabilities 声明） ——
    async def fetch_history(self, conversation_id: str, since: datetime) -> list[InboundMessage]: ...
    async def upload_media(self, file: bytes, mime: str) -> MediaRef: ...
    async def add_tag(self, customer_id: str, tag: str) -> None: ...
```

```python
@dataclass
class ChannelCapabilities:
    """子类声明自己支持哪些能力，Orchestrator/CS Reply Agent 据此决策。"""
    supports_text: bool = True
    supports_image: bool = False
    supports_voice: bool = False
    supports_card: bool = False           # 卡片消息
    supports_proactive_send: bool = False # 是否能主动发起会话
    supports_history_fetch: bool = False  # 是否能拉取历史消息
    max_message_length: int = 2000
    rate_limit_per_minute: int | None = None
```

#### 3.1.2 统一消息 Schema

```python
@dataclass
class InboundMessage:
    channel_id: str                    # 来自哪个 adapter
    conversation_id: str               # 平台无关的会话 ID（adapter 负责映射）
    customer_id: str                   # 平台无关的客户 ID
    sender_kind: Literal["customer", "agent_human", "system"]
    content: list[ContentPart]         # 多模态：text/image/file/card 子片段
    timestamp: datetime
    raw_payload: dict                  # 原始 payload 留档，用于 Replay 与排查
    platform_meta: dict                # 平台特有字段（企微 open_kfid、飞书 chat_id）
```

```python
@dataclass
class OutboundAction:
    conversation_id: str
    kind: Literal["reply", "add_tag", "add_to_crm", "transfer_to_human", ...]
    content: list[ContentPart] | None
    target: str | None                 # add_tag 的 customer_id 等
    metadata: dict
```

#### 3.1.3 设计要点

1. **Adapter 不感知业务**：只做协议翻译，不调 LLM、不做意图分类、不写 Memory。业务逻辑在 Orchestrator/Worker
2. **Capabilities 显式声明**：上层通过 `capabilities.supports_image` 决策，避免硬编码"如果是企微就……"
3. **平台特有字段统一进 `platform_meta`**：不污染主 schema；需要时下游显式取
4. **回调安全统一在基类**：签名校验、重放保护、解密这些跨平台共性逻辑提到基类（或公共 mixin），子类只实现平台特定算法
5. **OutboundAction 必须带 ExecutionToken 才执行**：与 §3.7 ToolProvider 同样的硬边界——Adapter 也是受 Harness 管的副作用出口

### 3.2 Social Perception
- **职责**：多模态解析、多轮上下文重建、会话状态机（新客户 / 跟进中 / 售后 / 投诉）
- **MVP**：仅文本 + 简单会话状态分类（图片 OCR 推到 v1）
- **会话隔离策略**：借 OpenClaw——私聊合并到主 session、群聊按上下文隔离
- **对外接口**：`PerceivedContext`

### 3.3 Social Brain / Orchestrator
- **职责**：意图分类 → 派发 Worker / 组队 / Proactive 触发
- **核心抽象**：`Intent`、`Task`、`DelegationPlan`
- **MVP 实现**：规则 + LLM 混合路由（规则快速命中，不明确时 LLM 兜底）

### 3.4 Worker Agents

**MVP 范围（2 个）**

| Worker | 职责 | 工具依赖 |
|---|---|---|
| **CS Reply Agent** | 生成回复、产出 ActionPlan（不直接调 tool） | Memory + 只读 CRM Tools + Knowledge |
| **Approval Router Agent** | 识别高风险动作、路由人审、管理审批队列 | HITL UI + AuditLog |

**v1 加入**

| Worker | 职责 | 工具依赖 |
|---|---|---|
| **CRM Explorer Agent** | 探索新 CRM / 修复失效 tool / 生成新 tool | Playwright sandbox + API client + ToolProvider |
| **Knowledge Agent** | 长期知识检索与维护 | Memory + 向量检索 |

每个 Worker：独立 context、独立 skill 空间、通过 Memory 协作；**所有副作用动作必须通过 Harness 提交 ActionPlan，不持有 ToolProvider 引用**。

### 3.5 Skills Repo
- **结构**：`skills/{bundled,workspace,learned}/<skill-name>/SKILL.md`（目录结构一开始就保留三类，便于 v1 平滑加入）
- **触发**：关键词 + 语义检索混合（MVP 仅关键词，语义检索随向量检索 v1 开启）
- **渐进披露**：借 Hermes 思路，skill 按需加载以节省 context
- **MVP**：仅 `bundled`（内置客服流程，手工编写 + Evolution 走 Skill 维度 Proposal）；`learned` 自动沉淀推到 v1

### 3.6 Memory
- **三层写入模型**（按延迟与审批要求区分）：
  - **L0 — Raw Event Store**：原始消息、tool 调用、决策事件，append-only，**实时直写**，不走 Evolution
  - **L1 — Ephemeral Session State**（`WORKING.md`）：当前会话短期状态，**实时直写**，会话结束 TTL 过期或归档
  - **L2 — Long-term Memory**（`MEMORY.md` / `CUSTOMER_<id>.md` / `USER.md` / `PRODUCT_KB.md`）：长期沉淀，**全部写入走 Evolution 层（Proposal + Gate）**
- **检索**：MVP 仅 FTS5；向量检索（`sqlite-vec` / Qdrant 可插拔后端）推到 v1
- **HITL 触发条件**（L2 写入）：包含 PII、金额、承诺、合规敏感、客户画像关键字段时强制人审；其他可走 Self-evolve（详见 §4.3）
- **L0 → L2 沉淀**：由后台 Consolidation 进程按规则/agent 触发，不阻塞会话路径

### 3.7 ToolProvider
- **三种 Provider**（MVP 仅 `APIToolProvider`，其余推到 v1）：
  - `APIToolProvider` **[MVP]**：基于 OpenAPI/schema 自动生成
  - `UIToolProvider` **(v1)**：基于 Playwright 录制 + DOM 快照生成
  - `MCPToolProvider` **(v1)**：直接接入 MCP server
- **统一接口**：`Tool.describe() / .call(args, execution_token) / .dry_run(args) / .health_check()`
  - `call` 必须携带 `ExecutionToken`（由 ActionGuard 签发，含过期时间、tool_id 绑定、args hash 绑定）
  - `dry_run` 仅允许只读路径，不签发 token
- **生命周期**：由 Evolution 层管理（创建 / 升级 / 废弃）
- **执行入口收敛**：Worker Agent 不持有 `ToolProvider` 引用，只能向 Harness 提交 `ActionPlan`

### 3.8 Harness / ActionGuard
- **分级策略（MVP 默认）**：
  - **Green**：只读（查 CRM、查记录）→ 自动执行
  - **Yellow**：低风险写（打标签、加备注、内部状态变更）→ 自动执行 + 事后审计
  - **Orange-A（模板化外发）**：命中已审通过的回复模板（变量替换） → 自动发送 + 限流 + 事后审计
  - **Orange-B（中风险写）**：改客户字段、改 CRM 业务数据 → 自动执行但限流 + 异步审核
  - **Orange-C（自由生成外发）**：LLM 自由生成的客户面文案 → **MVP 默认同步 HITL**；只有同时满足 ① 置信度 ≥ 阈值 ② 敏感词检测通过 ③ 承诺/金额/法律措辞检测通过 ④ 团队策略允许，才可降级为自动发送
  - **Red**：高风险（金额、承诺、退款、工单升级、群发消息、跨客户操作）→ 同步 HITL 审批
- **策略配置化**：每个团队可覆盖。策略变更的审批路径：
  - **MVP**：策略文件由 admin 手工编辑，变更必须经 HITL 审批面板确认（不走 Evolution Proposal，因为 MVP 未启用 Prompt/Config 维度）
  - **v1**：策略纳入 Evolution `Prompt/Config` 维度，统一走 Proposal + Gate
- **关键原则**：客户面外发（Orange-A/C 与 Red）是不可撤销副作用，事后审核不能阻止已发风险内容；MVP 期间任何"自由生成 → 自动发送"路径必须有结构化前置守卫，不能只靠后置审计

### 3.9 Evolution 层
详见 §4。

### 3.10 Replay（badcase 修复验证）

**核心用途**：**给定一条线上 badcase trace + 一组修复（改后的 skill / prompt / tool / memory），重放验证 badcase 是否消失、是否引入新问题。** Replay 是修复闭环的验证手段，不是单纯的"调试观察"工具。

**修复-验证闭环**：

```
线上 badcase trace
       ↓
人工/agent 诊断根因
       ↓
产出修复 Proposal（改 skill / prompt / tool / memory）
       ↓
Replay 用同一份输入 + 修复后的 artifact 重跑
       ↓
与原 trace diff：badcase 消失？无新增 regression？
       ↓
通过 → Proposal 进 PromotionGate；不通过 → 回到诊断
```

> **关键设计**：Replay 与 Evolution 是同一个闭环。修复本身就是 Proposal，**Replay 是这个 Proposal 的强制验证步骤**。

#### 3.10.1 三种回放模式（按用途排序）

| 模式 | 用途 | LLM | Tool | 主要消费者 |
|---|---|---|---|---|
| **What-if Replay**（核心） | **验证修复是否解决 badcase** | 真实重跑（带 override 的 prompt/skill/model） | 默认走缓存；指定的"被修复 tool"真实重跑 | 修复者、Evolution PromotionGate |
| **Strict Replay** | 完整复现 trace 当时的决策路径，用于人工诊断 | 全部命中缓存 | 全部命中缓存 | 排查阶段 |
| **Partial Replay** | A/B 对比"换 prompt / 换模型"是否更好 | 真实重跑 | 走缓存 | 模型/prompt 调优 |

#### 3.10.2 设计原则

1. **零侵入采集**：Replay 数据不靠业务代码主动写，在 Harness、ToolProvider、LLM 客户端三个边界统一拦截、追加到 trace
2. **确定性优先**：所有非确定输入（LLM 输出、tool 响应、时间戳、RNG）打 `recording_id` 进 trace；回放时按 id 命中缓存
3. **Override 必须显式且最小化**：What-if Replay 要求声明"改了哪些 artifact 版本"，未声明的一律走缓存，避免修复 A 时无意中也跑了新版本 B 干扰结论
4. **隔离执行**：Replay 进程默认 `--read-only` 启动 Harness，外部副作用记录但**不真正发出**（消息不发、CRM 不写）；只有 CI 压测场景可显式开 `--allow-side-effects`
5. **Diff 是一等公民**：Replay 结果不是"成功/失败"二元，而是与基线 trace 的结构化差异（哪条 ActionPlan 变了、哪个回复内容变了、哪个 tool 调用消失/新增）

#### 3.10.3 核心数据结构

```
ReplaySession {
  source_trace_id: <Langfuse trace id>,
  scope: [Conversation | SingleTurn | SingleAgentCall | SingleToolCall],
  mode: [WhatIf | Strict | Partial],
  overrides: {                         # What-if 必填、Strict 必空
    prompt_version?: <id>,
    skill_version?: <id>,
    tool_version?: <id>,
    model?: <model_id>,
    memory_l2_version?: <version_id>
  },
  diff_baseline: <source_trace_id>,
  result: ReplayResult {
    actions, llm_calls, tool_calls,
    divergence_points: [               # 与基线的结构化 diff
      { step, kind: [ActionChanged|ContentChanged|ToolMissing|ToolAdded], before, after }
    ],
    verdict: [BadcaseFixed | BadcaseRemains | NewRegression | Inconclusive]
  }
}
```

**Memory 时点重建**：
- L0（raw event）：append-only，按 conversation_id + 时间游标重放，天然支持任意时点
- L1（ephemeral session state）：视为 L0 的投影，Replay 时按 L0 重建，无独立存储
- L2（long-term memory）：每次 Evolution 提交生成一条不可变 `memory_version` 记录（应用层 CoW）；trace 里只存 `l2_version_at_t`，Replay 按 `WHERE version_id <= V` 读取

每条 trace 在关键节点（首条消息、Worker 派发、ActionPlan 提交、Tool 调用前）记录轻量 `ReplayCheckpoint { l0_cursor, l2_version, rng_seed, llm_recording_ids }`——只是几个 ID，不是数据快照。

#### 3.10.4 与既有模块的关系

| 模块 | Replay 复用 | 增量工作 |
|---|---|---|
| **AuditLog** | 决策事件流的真源 | 无 |
| **Langfuse trace** | LLM 调用 + tool 调用 + 中间状态 | 给每条 trace 补 `recording_id` 字段 |
| **Memory L0** | 原始事件 append-only，天然可重建 | 无 |
| **Memory L1** | 视为 L0 投影，按事件重建 | 无（不存独立快照） |
| **Memory L2** | 每次 Evolution 提交即版本提交 | 加 `version_id` 列；当前表变为 `current` 视图 |
| **ToolProvider** | 接口已统一 | 加 `ReplayingToolProvider` 装饰器：从 trace 命中缓存 / 透传真实调用 |
| **LiteLLM 客户端** | 已是单一出口 | 加 `ReplayingLLMClient` 装饰器：同上 |
| **Harness** | 统一执行入口 | 加 `--read-only` / `--allow-side-effects` 启动开关 |
| **Shadow Runner（§4.2）** | Shadow 本质就是 Partial Replay 的子集 | Shadow 改为调用 Replay 引擎，不再有两套实现 |

> **关键判断**：Shadow Runner 与 Replay 的差异只是触发时机（晋升前 vs 修复后），底层引擎只有一份。MVP 直接按 Replay 引擎建，Shadow 是它的一个调用入口。

#### 3.10.5 入口与工作流

- **Badcase 修复面板（Web UI 主入口）**：
  1. 从 trace 列表选中一条标记为 badcase 的 trace
  2. 创建修复 Proposal（改 skill / prompt / tool / memory）
  3. **强制 Replay 验证**：以该 Proposal 的 override 跑 What-if Replay，自动 diff 出 verdict
  4. `BadcaseFixed` + 无 `NewRegression` → Proposal 进 PromotionGate；否则回退修改
- **CLI**：`opencs replay <trace_id> --override skill=<id> [--read-only]`
- **API**：`POST /replays`——供 Evolution 层在 PromotionGate 内部自动调用，以及 CI 跑历史 badcase 套件

#### 3.10.6 MVP 范围

- ✅ **What-if Replay（核心）**：支持 skill / prompt / tool / memory L2 version 四类 override
- ✅ Strict Replay：用于人工诊断
- ✅ Partial Replay：用于 prompt/model 调优
- ✅ Conversation 与 SingleTurn 两个 scope
- ✅ Read-only 默认；Web UI（修复面板） + CLI + API 三入口
- ✅ Memory L0 事件重建 + L2 版本回溯
- ✅ 结构化 Diff + Verdict（`BadcaseFixed / BadcaseRemains / NewRegression / Inconclusive`）
- ✅ Evolution 集成：修复 Proposal 必须附带 Replay verdict 才能进 PromotionGate
- ❌ 批量 replay / 历史 badcase 回归套件 → v1
- ❌ Verdict 自动评估接 DeepEval（MVP 用规则 + 人工确认）→ v1
- ❌ SingleAgentCall / SingleToolCall scope → v1

---

## § 4. Dual-Track Evolution 详解

### 4.1 核心数据模型

```
Proposal {
  id, dimension: [Skill|Memory|Prompt|CRMTool|Signal],
  action: [Create|Update|Deprecate],
  payload: <具体变更内容>,
  evidence: <触发这次提案的信号数据>,
  confidence: 0-1,
  risk_level: [Low|Medium|High|Critical],
  shadow_result: <影子测试结果（可空）>,
  gate_decision: [AutoPromote|HITLPending|Rejected],
  reviewer: <人类审批者 id（如走 HITL）>,
  audit_trail: [events...]
}
```

**所有变更都是 Proposal——不存在绕过 Proposal 的 write 路径。**

### 4.2 生命周期

```
信号收集（Signal Loop）
        ↓
   提案生成（agent 或规则）
        ↓
   影子测试（Shadow Runner，不影响生产流量）
        ↓
   ┌─────────────────┐
   │ PromotionGate   │  ← 策略：阈值 + 风险 + 置信 + 合规标签
   └────┬──────┬─────┘
   Auto │      │ HITL
        ↓      ↓
   自动晋升  人审队列 → 人类决定 → 晋升/拒绝/改后再审
        ↓            ↓
    生效 + AuditLog 记录（两条路径都要记录）
        ↓
    后续信号反馈（闭环）
```

### 4.3 5 维度的 MVP 默认策略

> **MVP 范围**：仅启用前三维（Skill / Memory / CRM Tool）；Prompt/Config 与 Signal-Loop 推到 v1（详见 §7）。表格保留是为了固定后续 v1 的目标策略，避免重新设计。

| 维度 | Self-evolve（自动晋升条件） | HITL（必须人审条件） | MVP 启用 |
|---|---|---|---|
| **Skill 自创建** | 3+ 次成功案例 + 无副作用 tool 调用 + shadow 通过 | 涉及 Orange/Red 动作的 skill | ✅（仅 bundled skill 修改走 Proposal；learned skill 自动沉淀 v1） |
| **Memory Consolidation** | 重复访问 ≥5 次 + 非 PII + 非合规敏感 | 包含 PII、金额、承诺、客户画像关键字段 | ✅（仅 L2 长期层） |
| **CRM Tool 自进化** | 新端点探索 + schema 稳定 + dry_run 成功 3 次 | 首次接入新 CRM / 涉及写操作的新 tool | ⚠️ MVP 仅手工配置 + 只读 tool 走 Proposal；自动探索 v1 |
| **Prompt/Config 自调优** | **任何 prompt 改动都强制 HITL** | 全部 | ❌ v1 |
| **Signal Loop** | 新增被动信号源（埋点、回调） | 信号权重调整、反馈策略变更 | ❌ v1 |

**核心安全线**
- **Prompt 自调优默认全走 HITL**：MVP 不信任自动晋升
- **涉及客户数据的 Memory 默认全走 HITL**：合规第一
- **策略本身是 Evolution 的对象**：调整策略本身也要审批

### 4.4 与 Customer-action Harness 的关系

系统有**两套 Guardrail**，共享基础设施：

```
                ┌─────────────────┐
                │ ProposalQueue   │
                │ + AuditLog      │ ← 共享
                │ + HITL UI       │
                └────┬────────────┘
                     │
       ┌─────────────┴──────────────┐
       │                            │
┌──────▼──────────┐       ┌─────────▼────────┐
│ ActionGuard     │       │ EvolutionGate    │
│ (客户面动作)     │       │ (自我修改)        │
│ Green/Yellow/   │       │ Skill/Memory/    │
│ Orange/Red      │       │ Prompt/Tool/     │
│                 │       │ Signal           │
└─────────────────┘       └──────────────────┘
```

两者都是「提案 → 门控 → 执行 → 审计」模式，UI 和基础设施完全复用。

### 4.5 可观察性

- **Evolution Dashboard**：所有 proposal 的状态、按维度分类、按 risk 过滤
- **Audit Trail**：每个 proposal 完整生命周期事件流
- **回滚机制**：每次晋升记录 `previous_version`；MVP 只做 skill / tool / memory 的回滚，prompt 回滚 v2

---

## § 5. 外部系统对接

> **架构基线**：所有 IM 平台都是 `ChannelAdapter` 子类（接口见 §3.1.1）。本节描述 MVP 与 v1 的具体子类实现要点。

### 5.1 WecomCustomerServiceAdapter（MVP）
- **对接模式**：「微信客服」官方 API（B2C 外部客户 1-on-1 会话）
- **接入步骤**：企业认证 → 开通「微信客服」应用 → 配置回调 URL → 下发加密密钥
- **接口实现**：
  - `parse_inbound`：回调 URL 收到加密通知 → 解密（`wechatpy`） → 查询消息 API 拉取明文 → 映射到 `InboundMessage`，`open_kfid` / `external_userid` 进 `platform_meta`
  - `send`：校验 `ExecutionToken` → 调发送消息 API → 记录 AuditLog
  - `capabilities`：text=True, image=True, card=True, proactive_send=False, history_fetch=False
- **合规**：「会话存档」API 作为**可选合规留存能力**（独立于消息收发主链路），按团队合规要求开启，不作为消息收发的兜底通道

### 5.2 WebChatAdapter（MVP，内部调试用）
- 用途：内部 QA、Replay、本地开发调试，不对外
- WebSocket 长连 + 简单 token 鉴权；`capabilities` 全开（最大化覆盖测试场景）

### 5.4 FeishuAdapter（v1）
- 事件订阅 + bot 消息 API；签名/解密在基类公共 mixin 上覆盖飞书算法
- `capabilities` 与企微基本对齐；`platform_meta` 装 `chat_id` / `open_id`

### 5.5 CRM 对接

> **MVP 范围（5.5.1）**：仅手工配置 + 只读 API tool。
> **v1 范围（5.5.2 起）**：自动探索引擎（API 优先 + UI 兜底）+ 写工具 + 失效自愈。本节完整描述 v1 目标，便于 MVP 接口设计向前兼容。

#### 5.5.1 MVP：手工配置 + 只读 API tool

**接入流程**：
1. 用户在 Admin UI 填：CRM base URL + 静态 OpenAPI/swagger 文件（或粘贴 schema JSON）
2. 系统按 schema 为每个**只读** endpoint 生成 `Tool`（`GET` 路径或显式标记 read-only）
3. 每个 tool 自动 `dry_run` 验证 → 提交 Proposal → HITL 确认启用
4. 启用后 tool 对 CS Reply Agent 可见

**关键约束**：
- 写工具一律不在 MVP 启用——即使 schema 里有 `POST/PUT/DELETE`，生成阶段过滤掉
- 不调用 LLM 探索、不启动 Playwright、不使用 super-token

#### 5.5.2 v1：CRM 自动探索（核心差异化）

**接入流程**（用户视角）：
1. 用户在 Admin UI 填：CRM 入口 URL + super-token（或账号密码）
2. 系统触发 `CRMExplorerAgent` 启动探索任务
3. 探索任务输出：能力清单 + 自动生成的 tool 集合 + 测试报告
4. 用户在 Admin UI 确认要启用哪些 tool（这一步是 HITL 晋升门）
5. 启用后 tool 对 CS Reply Agent 可见

**探索引擎双栈**：

- **API-first 路径（优先）**：
  1. 探测常见 schema 入口（`/openapi.json`, `/swagger.json`, `/graphql`, `/api/schema`）
  2. 若找到 → 解析 schema → 为每个 endpoint 生成 `Tool`（带 JSON-schema 输入/输出）
  3. 对每个生成的 tool 做 `dry_run` 验证（只测 GET / 读操作）
  4. 提交 Proposal 到 Evolution 层

- **UI fallback 路径**（API 走不通时）：
  1. 启动 Playwright 容器 → 登录 CRM
  2. **生产环境探索默认仅限只读路径**：发现页面结构、读字段、抓 schema；禁止模拟改字段 / 提交表单 / 删除等写操作
  3. 写工具的录制必须在以下任一环境完成：① 测试租户 ② CRM 沙箱 ③ 标记为只读账号的环境（账号本身无写权限作为兜底）
  4. 每步录制 DOM 快照 + 视觉截图 + 用户动作（click/fill/select）
  5. 把一组「导航路径 + 动作序列」抽象为 `UITool`
  6. **写类 UITool 强制要求**：在非生产环境完成回放 + dry_run 通过 → Proposal → **HITL 人工确认** → PromotionGate；只读 UITool 可走标准 Evolution 路径
  7. **super-token 使用约束**：仅在 Explorer 任务窗口内解密注入 sandbox，任务结束立即失效；每次使用完整审计；不允许长驻进程持有

**工具失效检测**：
- 每个 tool 周期性 `health_check`
- 失败 → 标记 `deprecated` + 触发 CRMExplorer 自动修复（重新探索对应能力）

---

## § 6. 部署与安全边界

### 6.1 部署形态
- **MVP 默认**：Docker Compose（单机，适合试点团队）
- **生产**：K8s Helm chart（v1）
- **组件**：
  - `gateway`（FastAPI，接 channel 回调 + Admin API）
  - `orchestrator`（agent 运行时）
  - `worker-pool`（Worker agents，可横向扩展）
  - `tool-sandbox`（Playwright 容器池，隔离 UI 探索）
  - `evolution`（后台任务 + ProposalQueue 消费者）
  - `postgres`（主数据）、`redis`（队列 + 缓存）、`sqlite + sqlite-vec`（本地记忆存储，可替换为 Qdrant）
  - `langfuse`（self-hosted，trace + HITL 队列底座）
  - `web-ui`（Next.js / React 前端）

### 6.2 Sandbox 层级
- **ToolProvider 执行**：
  - API 调用：进程内执行（无敏感副作用，只靠 ActionGuard 拦截）
  - UI 探索：**强制独立 Docker 容器**（Playwright sandbox，drop capabilities、只读 root、PID 限制，借 hermes container hardening）
- **Skill 执行**：和主 agent 同进程（skill 本身是声明式，不执行任意代码）

### 6.3 Secrets 管理
- **MVP**：本地加密存储（使用 `cryptography` + 主密钥），数据库字段加密
- **v1**：HashiCorp Vault / 企业 KMS 可插拔后端
- **super-token 特殊处理**：CRM super-token 仅在 Explorer 任务期间解密 + 注入 sandbox；主进程内存不长期持有明文

### 6.4 Audit & 合规
- **AuditLog**：append-only，所有 ActionGuard/EvolutionGate 决策记录
- **PII 脱敏**：prompt 发给 LLM 前过一层 redaction（手机号、身份证号、地址默认脱敏）
- **数据驻留**：全部数据存本地（自托管），LLM 调用可配置「本地模型优先、敏感路径禁外发」

### 6.5 模型 Provider 策略
- 统一走 **LiteLLM** 抽象层
- **MVP 默认支持**：Anthropic Claude、OpenAI、以及国内主流模型（通义 / 文心 / Kimi / DeepSeek）
- **Per-task model routing**：高敏感任务（PII 相关、金额相关）可强制走本地 / 私有化模型

### 6.6 MVP 默认依赖清单（OSS 复用决策）

> **原则**：能用成熟 OSS 解决的不自建；自建集中在产品差异化（ActionGuard / Evolution / CRM Explorer）。本节作为进入 `writing-plans` 时各 phase 的技术选型基线，避免逐个 phase 重新决策。

#### A. 直接复用（MVP 默认依赖）

| 领域 | 选型 | 用途 |
|---|---|---|
| 企微对接 | `wechatpy` | 回调加解密、签名校验、access_token 管理；不自己写 |
| 模型抽象 | `LiteLLM` | 多 provider 统一接口、per-task routing |
| 全文检索 | SQLite `FTS5`（内置） | Memory L2 关键词检索 |
| 向量检索 | `sqlite-vec` | 取代原 spec 中的 `sqlite-vss`（已停更）；v1 可换 Qdrant |
| PII 脱敏 | `Microsoft Presidio` + 自写中文 recognizer（手机号 / 身份证 / 地址） | §6.4 redaction 层 |
| OCR | （MVP 不做，v1 引入 `RapidOCR` 或 `PaddleOCR`） | §3.2 图片解析 |
| 后台任务队列 | `arq`（Redis 后端） | Proposal 处理、Consolidation、health_check |
| Trace + HITL 队列 | `Langfuse` self-hosted | LLM trace、Evolution 一期 Dashboard、人审队列底座 |
| 数据校验 | `pydantic` v2 | `InboundMessage` / `ActionPlan` / `Proposal` schema |
| 加密存储 | `cryptography` + SQLAlchemy `EncryptedType` | §6.3 secrets at rest |
| 状态机 | `transitions` | §3.2 会话状态机（新客户 / 跟进 / 售后 / 投诉） |
| Web 框架 | `FastAPI` | gateway / Admin API |
| 前端组件库 | `shadcn/ui` + `TanStack Query` + `react-hook-form` | Admin Web UI |
| 浏览器自动化 | `Playwright`（v1 加 `browser-use` 用于 Explorer） | UIToolProvider 录制与回放 |
| 容器加固 | 复用 hermes container hardening 模式（drop caps / 只读 root / PID 限制） | tool-sandbox |

#### B. 借抽象（参考但不直接依赖）

| 领域 | 参考项目 | 借什么 |
|---|---|---|
| Orchestrator 状态机 | `LangGraph` | StateGraph + checkpoint 抽象；不直接 fork |
| Skill 规范 | Anthropic Claude Skills、`OpenHands` AgentSkills | Markdown + frontmatter 目录结构 |
| Channel Adapter 接口 | `Errbot` / Botbuilder | 多通道适配抽象 |
| 评估 / 回归 | `DeepEval` 或 `promptfoo`（v1 引入） | shadow 对比与回归测试 |
| ActionGuard 策略外置 | `OPA`（Open Policy Agent） | MVP 可暂用代码实现，但接口按"策略外置"设计，v1 切到 OPA 不破坏架构 |

#### C. 必须自建（产品差异化，无合身 OSS）

| 模块 | 原因 |
|---|---|
| ActionPlan / ExecutionToken 类型系统 | 安全边界核心，必须自控（基于 pydantic + 短期签名 token） |
| Proposal 数据模型 + PromotionGate 逻辑 | 双轨进化是核心差异化 |
| Memory L0→L2 Consolidation 规则 | 含业务语义（PII / 承诺 / 金额识别），需绑定 §6.4 PII 规则 |
| CRM Explorer Agent（v1） | 没有成熟"自动探索 + tool 生成"OSS；用 browser-use + LangGraph 拼装 |
| 企微客服会话归并与分配业务层 | wechatpy 只到 API；会话归并、客服路由是产品逻辑 |

#### D. 选型变更说明
- `sqlite-vss` → `sqlite-vec`：vss 已不再维护，vec 是同作者继任项目，API 相近，迁移成本低
- 原 spec 未指定的：队列（`arq`）、状态机（`transitions`）、PII（`Presidio`）、Trace（`Langfuse`）—— 都在本节锁定，进 plan 时不再重选

---

## § 7. MVP 范围 vs 后续 Roadmap

### 7.1 MVP（P0，本 spec 覆盖范围）

**MVP 范围原则**：先跑通**可审计的最小客服闭环**，再逐步打开自进化与自动探索能力。

**必须有（最小可审计闭环）**
- [x] Channel Gateway：企微客服接口 + WebChat
- [x] Social Perception：文本（图片 OCR 推迟到 v1）；简单会话状态机
- [x] Orchestrator + 2 Worker（**CS Reply**、**Approval Router**）
- [x] Skills Repo：bundled only（learned skill 自动沉淀推到 v1）
- [x] Memory：三层写入模型 + FTS5 检索（向量检索推到 v1）
- [x] ToolProvider：**仅 API 类**（UIToolProvider / MCPToolProvider 推到 v1）
- [x] CRM 对接：**仅手工配置 + 只读 API tool**（自动探索/UI fallback/写工具推到 v1）
- [x] Harness / ActionGuard：完整分级（Green / Yellow / Orange-A/B/C / Red）+ ExecutionToken
- [x] Evolution 层（**MVP 收敛**）：仅 Skill / Memory / Tool 三个维度的 Proposal + HITL UI + AuditLog；Prompt/Config 与 Signal-Loop 维度推到 v1
- [x] **Replay 引擎**：核心 What-if 模式（验证 badcase 修复）+ Strict/Partial 辅助；Conversation/SingleTurn scope；read-only 默认；Memory L0 重建 + L2 版本回溯；结构化 diff + verdict
- [x] **Replay × Evolution 集成**：修复 Proposal 必须附带 Replay verdict 才能进 PromotionGate
- [x] Admin Web UI：HITL 审批面板 + AuditLog 查看 + **Badcase 修复面板（Replay 主入口）** + CRM 手工配置向导（Evolution Dashboard 简化版）
- [x] Docker Compose 一键部署

**v1 收编（原 P0 中推迟的部分）**
- 图片 OCR、CRM Explorer Agent、UIToolProvider、MCPToolProvider
- CRM 自动探索（API 优先 + UI 兜底）
- learned skill 自动沉淀
- 完整 5 维 Evolution（Prompt 自调优、Signal-Loop 自演化）
- 完整 Evolution Dashboard、向量检索

### 7.2 v1（MVP 之后 3 个月）
- 上述「v1 收编」全部内容（OCR、CRM Explorer、UI/MCP ToolProvider、自动探索、learned skill、5 维 Evolution、向量检索、完整 Dashboard）
- Replay 增强：批量 replay、历史 badcase 回归套件、Verdict 自动评估接 DeepEval、SingleAgentCall/SingleToolCall scope
- 飞书群接入
- UI fallback 探索能力完善（更鲁棒的元素定位、失效自愈）
- Skill Registry（可从社区导入 skill）
- K8s Helm chart

### 7.3 v2（6 个月后）
- Memory Dreaming（后台 consolidation 进阶）
- Prompt 自调优（带严格 guardrail）
- 多租户 SaaS 模式
- 客诉工单模块（独立子系统）

### 7.4 v3 及之后
- 主动外呼 / 营销触达（Proactive Agent）
- 群运营 Agent（社群答疑、活动管理）
- Agent 间直接通信（v3 打开 Worker-to-Worker 直连）
- 语音通道（借鉴 Hermes Voice Workflows）

---

## § 8. Open Questions / 待确认事项

所有原问题已在迭代中降级——选型已锁定或转化为前向兼容约束。本节保留作为决策履历，不阻塞进入 writing-plans。

1. ~~**企微客服接口的具体 scope**~~ — 已降级：`ChannelAdapter` 抽象（§3.1.1）就位后，「微信客服」官方 API vs「企业应用 + 外部联系人」是 `WecomCustomerServiceAdapter` 子类的内部选型，不影响架构。MVP 默认走「微信客服」官方 API；如团队无认证主体，phase 1 设计时再加 `WecomEnterpriseAppAdapter` 兄弟子类

2. ~~**UI 框架选型**~~ — 已在 §6.6 锁定：Next.js + shadcn/ui + Tailwind

3. ~~**向量存储 MVP 选型**~~ — 已在 §6.6 锁定：MVP 不做向量检索；v1 引入 `sqlite-vec`（轻量）或 `Qdrant`（部署略重但伸缩性更好），按届时数据量决定

4. ~~**国产化 / 私有化要求**~~ — 已降级：MVP 不强制信创（Postgres + Redis + SQLite + LiteLLM 国内模型即可）。**前向兼容约束**：DB 层不用 Postgres 独有语法（`JSONB` 高级算子、`gen_random_uuid()` 等），SQLAlchemy 方言中性，便于 v1 接达梦 / OceanBase 不动业务代码

5. ~~**组织 / 权限模型**~~ — 已降级：MVP 走单组织 + 4 角色（owner / admin / reviewer / viewer）。**前向兼容约束**：`Customer` / `Conversation` 实体一开始就预留 `group_id` 字段（默认 NULL = 全组织可见），v1 按 group 加 ACL 时不动表结构

---

## § 9. 下一步

本 spec 通过后，进入 `writing-plans` 流程：将 §7.1 MVP 范围拆解为可实施的**阶段性计划**（建议阶段划分：Channel & Gateway → Agent Core + Harness/ActionGuard → Memory（三层） + bundled Skills → 只读 CRM API Tool → **Replay 引擎 + Memory 快照** → Evolution（Skill/Memory/Tool 三维，Shadow 复用 Replay） + HITL UI + AuditLog → 部署与运维）。

每个阶段独立成一个 plan 文档，按依赖顺序实施。
