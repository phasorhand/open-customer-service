# OpenCS

> 开源、可自托管的私域运营 AI 客服平台。  
> Open-source, self-hosted private-domain customer-service AI platform.

企微客服闭环 + CRM 自动对接 + 双轨进化（自动晋升 / HITL 审批）+ 一键 Docker 部署。

---

## 功能概览

| 模块 | 能力 |
|------|------|
| **Channel Gateway** | 企微客服 1-on-1 + WebChat 调试接口；统一 `ChannelAdapter` 抽象 |
| **Agent Core** | Orchestrator + CS Reply Worker + Approval Router；LiteLLM 模型抽象 |
| **ActionGuard** | 六级风控（Green / Yellow / Orange-A/B/C / Red）+ ExecutionToken 防重放 |
| **AuditLog** | SQLite 审计日志，记录每次工具调用决策 |
| **HITL Queue** | 高风险动作挂起，管理员在 Web UI 审批后执行 |
| **Skills Repo** | Markdown 技能文件 + FTS5 关键词匹配触发，Zero-shot 注入 |
| **Memory** | L0（原始对话）/ L1（摘要）/ L2（结构化知识）三层写入 + FTS5 检索 |
| **ToolProvider** | APIToolProvider：OpenAPI schema → 工具；read-only CRM API 调用 |
| **Replay Engine** | What-if / Strict / Partial 三种模式；baseline vs replay diff + verdict |
| **Evolution Layer** | Skill / Memory / CRM-Tool 三维 Proposal → ShadowRunner → Gate → HITL |
| **Admin API** | REST `/admin/*`：提案审批、审计日志、统计、CRM 配置 |
| **Admin Web UI** | Next.js 14：Dashboard、HITL 面板、Audit Log、Replay、CRM 向导 |
| **Docker Compose** | 一命令启动 5 个服务：api、web-ui、Langfuse、Postgres、Redis |

---

## 架构一览

```
企微 / WebChat
      │
      ▼
 ChannelGateway          ← WecomCSAdapter / WebChatAdapter
      │
      ▼
  Orchestrator           ← 驱动 Worker 循环
  ├── CSReplyWorker      ← LLM 生成回复
  └── ApprovalRouter     ← 高风险转人工
      │
  ActionGuard            ← 六级风控 + ExecutionToken
  ├── ToolExecutor       ← APITool（CRM 只读）
  ├── SkillRepo          ← FTS5 匹配 → 注入 prompt
  └── MemoryStore        ← L0/L1/L2 读写
      │
  AuditLog  HITLQueue
      │
  Evolution Layer
  ├── ProposalStore      ← SQLite 持久化
  ├── EvolutionGate      ← 置信度阈值 + ShadowRunner
  └── Handlers           ← Skill / Memory / CRMTool
      │
  Admin API + Web UI     ← 审批 / 查日志 / 触发 Replay / 配 CRM
```

---

## 快速开始

### 本地开发（无 Docker）

**前置：** Python 3.12、[uv](https://github.com/astral-sh/uv)

```bash
git clone https://github.com/phasorhand/open-customer-service.git
cd open-customer-service

uv sync --all-groups          # 安装所有依赖（含 dev）
uv run pytest                 # 运行测试（293 个）

# 启动 API（开发模式，热重载）
uv run uvicorn opencs.main:create_full_app --factory --reload
# → http://localhost:8000/docs
```

### Docker Compose（推荐）

**前置：** Docker 24+ with Compose v2，~4GB 可用内存

```bash
cp .env.example .env
# 编辑 .env：填写 ANTHROPIC_API_KEY（其他字段保持默认可本地运行）

docker compose up -d --build
./scripts/docker-smoke-test.sh   # 等待所有服务健康后自动验证
```

| 服务 | 地址 | 说明 |
|------|------|------|
| Admin Web UI | http://localhost:3000 | HITL 审批、日志、Replay、CRM |
| Backend API | http://localhost:8000/docs | FastAPI Swagger UI |
| Langfuse | http://localhost:3001 | 链路追踪（首次登录创建项目） |

**Langfuse 接入（可选）：**
1. 打开 http://localhost:3001，注册账号（第一个用户自动成为 Admin）
2. 创建项目，复制 Public Key / Secret Key
3. 填入 `.env` 的 `LANGFUSE_PUBLIC_KEY` 和 `LANGFUSE_SECRET_KEY`
4. `docker compose up -d opencs-api` 重启 API 即可

**数据卷管理：**
```bash
docker compose down      # 停止，保留数据
docker compose down -v   # 停止，清空所有数据
```

---

## 项目结构

```
.
├── src/opencs/
│   ├── agents/            # Orchestrator + Workers + LiteLLM 抽象
│   ├── channel/           # ChannelRegistry + WebChat / WecomCS 适配器
│   ├── evolution/         # ProposalStore、Gate、ShadowRunner、三维 Handler
│   ├── gateway/           # FastAPI app + routes（webchat/wecom/replay/admin）
│   ├── harness/           # ActionGuard、ExecutionToken、AuditLog、HITLQueue
│   ├── memory/            # MemoryStore（L0/L1/L2）+ FTS5
│   ├── replay/            # ReplayEngine、ReplayingLLMClient、Diff/Verdict
│   ├── skills/
│   │   └── bundled/       # 内置技能（greeting、refund_policy …）
│   ├── tools/             # ToolRegistry、APITool、ToolExecutor、MockCRM
│   ├── tracing/           # LangfuseClient + @observe 装饰器
│   └── main.py            # 生产入口：create_full_app()
├── web-ui/                # Next.js 14 Admin UI（见 web-ui/README.md）
├── tests/                 # pytest 测试套件（293 个）
├── scripts/
│   └── docker-smoke-test.sh
├── Dockerfile.api         # python:3.12-slim
├── Dockerfile.web         # node:20-alpine 三阶段构建
├── docker-compose.yml
└── .env.example
```

---

## 开发指南

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENCS_DATA_DIR` | `/data` | SQLite 数据库目录（Docker 内） |
| `LITELLM_MODEL` | `anthropic/claude-sonnet-4-20250514` | LLM 模型标识 |
| `ANTHROPIC_API_KEY` | — | LLM API Key |
| `LANGFUSE_HOST` | `http://langfuse:3000` | Langfuse 服务地址 |
| `LANGFUSE_PUBLIC_KEY` | — | 留空则不启用 Tracing |
| `LANGFUSE_SECRET_KEY` | — | 留空则不启用 Tracing |
| `REDIS_URL` | `redis://redis:6379` | Redis 连接（Compose 内） |
| `WECOM_CORP_ID` | — | 企微应用 Corp ID |
| `WECOM_TOKEN` | — | 企微回调 Token |
| `WECOM_ENCODING_AES_KEY` | — | 企微消息加解密 Key |

### 测试

```bash
uv run pytest                  # 全量（293 个）
uv run pytest tests/gateway/   # 仅 gateway 模块
uv run pytest -x -q            # 快速失败模式

cd web-ui && npm test          # Vitest 组件测试
cd web-ui && npm run typecheck # TypeScript 类型检查
```

### 代码质量

```bash
uv run ruff check src tests    # Lint
uv run ruff format src tests   # 格式化
uv run mypy                    # 类型检查（strict 模式）
```

### 新增技能

在 `src/opencs/skills/bundled/<skill-name>/SKILL.md` 创建文件，重启后自动加载：

```markdown
---
name: my_skill
description: 一句话描述这个技能的用途
keywords:
  - 关键词1
  - keyword2
---
技能正文：告诉 Agent 在触发此技能时应如何行动。
```

### 新增 API 工具

```python
from opencs.tools.api_tool import APITool
from opencs.tools.registry import ToolRegistry

reg = ToolRegistry()
reg.register(APITool(
    tool_id="crm.update_tag",
    base_url="https://your-crm.example.com",
    method="POST",
    path_template="/customers/{customer_id}/tags",
    parameters_schema={
        "customer_id": {"type": "string"},
        "tag": {"type": "string"},
    },
    read_only=False,  # False → Orange 风控，需要 HITL 或 ExecutionToken
))
```

---

## Evolution（自进化）工作流

```
1. 对话结束 → MemoryStore.write_l0() → 触发 evolution_hook
2. Handler 分析对话 → 生成 Proposal（Skill / Memory / CRM-Tool 三个维度）
3. EvolutionGate 评估：
   ├── 置信度高 + ShadowRunner (Replay) 通过 → auto_promote（自动晋升）
   └── 置信度低 / 高风险              → hitl_pending → 管理员审批
4. 审批通过 → Handler 执行变更（写技能文件 / L2 记忆 / 注册工具）
```

- **`/proposals`** — HITL 审批主入口，支持 status / dimension 过滤
- **`/replays`** — 手动触发 Replay，验证 badcase 修复效果后再晋升

---

## 路线图

| 版本 | 状态 | 内容 |
|------|------|------|
| **v1.0** | ✓ 已完成 | 企微客服闭环、HITL Evolution、Admin UI、Docker 部署 |
| **v1.1** | 规划中 | CRM Explorer Agent、UIToolProvider、向量检索、Feishu 群机器人 |
| **v2.0** | 待定 | 多租户 SaaS、Prompt 自调优、批量 Replay + DeepEval |
| **v3.0** | 待定 | 主动外呼、群运营 Agent、语音通道 |

---

## 许可证

[MIT](LICENSE)
