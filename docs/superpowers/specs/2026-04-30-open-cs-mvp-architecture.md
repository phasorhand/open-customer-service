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
- Agent 架构：**Orchestrator + Worker**（MVP 3 个 worker）
- CRM 探索：**API 优先 + UI 兜底**（双栈）
- Self-evolve 维度：**全 5 维**，严格区分 Self-evolve / HITL（**Dual-Track Evolution**）
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
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │ CS Reply     │ │ CRM Explorer │ │ Approval     │ │ Knowledge    │ │
│  │ Agent        │ │ Agent        │ │ Router Agent │ │ Agent (v2)   │ │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────────────┘ │
└─────────┼────────────────┼────────────────┼──────────────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼──────────────────────────┐
│           § 共享能力层（Skills / Memory / Tools / Harness）            │
│  ┌────────────┐ ┌────────────┐ ┌────────────────┐ ┌────────────────┐ │
│  │ Skill Repo │ │ Memory     │ │ ToolProvider   │ │ Harness /      │ │
│  │ (渐进加载)  │ │ (全局/会话)│ │ (API/UI/MCP)   │ │ ActionGuard    │ │
│  └────────────┘ └────────────┘ └────────────────┘ └────────────────┘ │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│               § Evolution 层（双轨进化 Self-evolve / HITL）             │
│   ProposalQueue  │  Shadow Runner  │  Promotion Gate  │  AuditLog     │
│   5 维度：Skill / Memory / Prompt&Config / CRM-Tool / Signal-Loop     │
└───────────────────────────────────────────────────────────────────────┘
```

**关键设计原则**

1. **每层只和相邻层通信**
2. **Evolution 层横切所有层**：只观察事件 + 产出 proposal，不直接改运行代码；所有晋升都走 ProposalQueue + PromotionGate
3. **Worker Agent 之间不直连**：必须通过 Orchestrator 或共享 Memory 协作
4. **Harness 包裹「所有对外副作用」**：任何改 CRM / 发消息 / 写文件 / 调外部 API 的动作都先经过 ActionGuard 分级

---

## § 3. 核心模块边界

### 3.1 Channel Gateway
- **职责**：统一接入层，规范化消息为 `InboundMessage` 事件
- **MVP 支持**：企微客服接口（B2C 外部客户 1-on-1）、WebChat（内部调试）
- **v2**：企微群机器人、飞书群、Telegram/Slack
- **对外接口**：`InboundMessage`（统一 schema）、`OutboundAction`（回复 / 加好友 / 打标签）
- **依赖**：Harness（出站动作必须走 ActionGuard）

### 3.2 Social Perception
- **职责**：多模态解析、多轮上下文重建、会话状态机（新客户 / 跟进中 / 售后 / 投诉）
- **MVP**：文本 + 图片 OCR；简单会话状态分类
- **会话隔离策略**：借 OpenClaw——私聊合并到主 session、群聊按上下文隔离
- **对外接口**：`PerceivedContext`

### 3.3 Social Brain / Orchestrator
- **职责**：意图分类 → 派发 Worker / 组队 / Proactive 触发
- **核心抽象**：`Intent`、`Task`、`DelegationPlan`
- **MVP 实现**：规则 + LLM 混合路由（规则快速命中，不明确时 LLM 兜底）

### 3.4 Worker Agents（MVP 3 个）

| Worker | 职责 | 工具依赖 |
|---|---|---|
| **CS Reply Agent** | 生成回复、决定 CRM 操作 | Memory + CRM Tools + Knowledge |
| **CRM Explorer Agent** | 探索新 CRM / 修复失效 tool / 生成新 tool | Playwright sandbox + API client + ToolProvider |
| **Approval Router Agent** | 识别高风险动作、路由人审、管理审批队列 | HITL UI + AuditLog |

每个 Worker：独立 context、独立 skill 空间、通过 Memory 协作。

### 3.5 Skills Repo
- **结构**：`skills/{bundled,workspace,learned}/<skill-name>/SKILL.md`
- **触发**：关键词 + 语义检索混合
- **渐进披露**：借 Hermes 思路，skill 按需加载以节省 context
- **MVP**：bundled（内置客服流程）+ learned（从成功案例沉淀）

### 3.6 Memory
- **分层**：
  - `WORKING.md`（当前会话短期）
  - `MEMORY.md`（全局长期事实）
  - `USER.md` / `CUSTOMER_<id>.md`（单客户档案）
  - `PRODUCT_KB.md`（产品知识库）
- **检索**：FTS5 + 向量（可插拔后端）
- **写入**：所有写入走 Evolution 层

### 3.7 ToolProvider
- **三种 Provider**：
  - `APIToolProvider`：基于 OpenAPI/schema 自动生成
  - `UIToolProvider`：基于 Playwright 录制 + DOM 快照生成
  - `MCPToolProvider`：直接接入 MCP server
- **统一接口**：`Tool.describe() / .call(args) / .dry_run(args) / .health_check()`
- **生命周期**：由 Evolution 层管理（创建 / 升级 / 废弃）

### 3.8 Harness / ActionGuard
- **分级策略（MVP 默认）**：
  - **Green**：只读（查 CRM、查记录）→ 自动执行
  - **Yellow**：低风险写（打标签、加备注）→ 自动执行 + 事后审计
  - **Orange**：中风险（改客户字段、外发文案）→ 自动执行但有限流 + 异步审核
  - **Red**：高风险（金额、承诺、退款、工单升级、群发消息）→ 同步 HITL 审批
- **策略配置化**：每个团队可覆盖；策略本身也是 Evolution 的对象

### 3.9 Evolution 层
详见 §4。

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

| 维度 | Self-evolve（自动晋升条件） | HITL（必须人审条件） |
|---|---|---|
| **Skill 自创建** | 3+ 次成功案例 + 无副作用 tool 调用 + shadow 通过 | 涉及 Orange/Red 动作的 skill |
| **Memory Consolidation** | 重复访问 ≥5 次 + 非 PII + 非合规敏感 | 包含 PII、金额、承诺、客户画像关键字段 |
| **Prompt/Config 自调优** | **任何 prompt 改动都强制 HITL**（MVP 原则） | 全部 |
| **CRM Tool 自进化** | 新端点探索 + schema 稳定 + dry_run 成功 3 次 | 首次接入新 CRM / 涉及写操作的新 tool |
| **Signal Loop** | 新增被动信号源（埋点、回调） | 信号权重调整、反馈策略变更 |

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

### 5.1 企微客服接口（MVP）
- **对接模式**：「微信客服」官方 API（B2C 外部客户 1-on-1 会话）
- **接入步骤**：企业认证 → 开通「微信客服」应用 → 配置回调 URL → 下发加密密钥
- **消息流**：
  - **Inbound**：回调 URL 收到加密通知 → 解密 → 查询消息 API 拉取明文 → 转 `InboundMessage`
  - **Outbound**：经 ActionGuard 分级 → 调发送消息 API → 记录 AuditLog
- **合规**：支持「会话存档」API 兜底（全量留存客户沟通记录）
- **对接抽象**：`WecomCustomerServiceAdapter` 实现统一 `ChannelAdapter` 接口，其他通道（飞书、WebChat）实现同一接口

### 5.2 飞书群（v2）
- 事件订阅 + bot 消息 API
- 接入模式与企微复用 `ChannelAdapter` 抽象

### 5.3 CRM 自动对接（核心差异化）

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
  2. 引导 agent 遍历导航、模拟典型操作（查客户、改字段）
  3. 每步录制 DOM 快照 + 视觉截图 + 用户动作（click/fill/select）
  4. 把一组「导航路径 + 动作序列」抽象为 `UITool`
  5. 同样走 dry_run → Proposal → PromotionGate

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
  - `postgres`（主数据）、`redis`（队列 + 缓存）、`sqlite + sqlite-vss`（本地记忆存储，可替换为 Qdrant）
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

---

## § 7. MVP 范围 vs 后续 Roadmap

### 7.1 MVP（P0，本 spec 覆盖范围）

**必须有**
- [x] Channel Gateway：企微客服接口 + WebChat
- [x] Social Perception：文本 + 图片 OCR，会话状态机
- [x] Orchestrator + 3 Worker（CS Reply、CRM Explorer、Approval Router）
- [x] Skills Repo（bundled + learned）
- [x] Memory 4 分层 + FTS5 检索
- [x] ToolProvider（API + UI + MCP 三种）
- [x] CRM 自动探索（API 优先 + UI 兜底）
- [x] ActionGuard 4 级分级
- [x] Evolution 层（5 维度 + 双轨门控 + HITL UI + AuditLog）
- [x] Admin Web UI：HITL 审批面板 + Evolution Dashboard + CRM 接入向导
- [x] Docker Compose 一键部署

### 7.2 v1（MVP 之后 3 个月）
- 飞书群接入
- UI fallback 探索能力完善（更鲁棒的元素定位、失效自愈）
- Skill Registry（可从社区导入 skill）
- K8s Helm chart
- 向量检索替换（Qdrant）

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

这些是 MVP 实施前需要最终拍板的问题，spec 暂按括号内默认值推进：

1. **企微客服接口的具体 scope**
   - 默认：「微信客服」官方 API（需要认证企业主体 + 开通微信客服应用）
   - 备选：「企业应用」+ 「外部联系人」 API（权限更广但无 1-on-1 客服会话原语）

2. **UI 框架选型**
   - 默认：Next.js + shadcn/ui + Tailwind（现代感强，开发效率高）
   - 备选：Ant Design（更偏企业中后台）

3. **向量存储 MVP 选型**
   - 默认：SQLite + sqlite-vss（单机简单）
   - 备选：直接上 Qdrant（部署略重但 v1 不用再换）

4. **国产化 / 私有化要求**
   - 默认：支持国内模型走 LiteLLM，不强制信创
   - 备选：是否需要首日就支持信创环境（麒麟 OS / 达梦 DB 等）

5. **组织 / 权限模型**
   - 默认：MVP 单组织多用户（owner / admin / reviewer / viewer 四角色）
   - 备选：是否需要按客户分组做 ACL

---

## § 9. 下一步

本 spec 通过后，进入 `writing-plans` 流程：将 §7.1 MVP 范围拆解为可实施的**阶段性计划**（建议阶段划分：Channel & Gateway → Agent Core → Memory & Skills → CRM Explorer → Evolution → UI & Ops）。

每个阶段独立成一个 plan 文档，按依赖顺序实施。
