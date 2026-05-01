# Memory 三层模型 · OSS 调研

## 目标
实现 OpenCS 的三层记忆存储（L0 原始事件 append-only / L1 会话临时状态 / L2 长期记忆 FTS5 检索），为 Worker Agent 提供会话上下文，不引入外部向量数据库（MVP 仅关键词检索）。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| SQLite FTS5（stdlib 内置） | Public Domain | — | — | 0KB | ✅ 直接用 | 内置于 Python sqlite3；FTS5 全文检索；§6.6 已锁定 |
| [sqlite-vec](https://github.com/asg017/sqlite-vec) | Apache-2.0 | 2026-03 | 3.2k | ~800KB | ⚠️ v1 | §6.6 锁定用于向量检索；MVP 不启用（纯 FTS5 已够） |
| [Qdrant](https://github.com/qdrant/qdrant) | Apache-2.0 | 2026-04 | 21k | 重 | ❌ MVP | 向量检索强，但部署较重；MVP 用 sqlite-vec v1 |
| [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) | MIT | 2026-04 | 10k | ~4MB | ❌ | 封装层过重；直接用 sqlite3 足够 |
| [transitions](https://github.com/pytransitions/transitions) | MIT | 2026-03 | 5.7k | ~400KB | ⚠️ 考察 | §6.6 已锁定用于会话状态机；MVP 中 L1 用简单 dict，状态机推到 Social Perception 模块 |

## 决策
- **复用**：SQLite FTS5（stdlib，零额外依赖）—— L0 / L2 底层存储
- **自建**：L0RawEventStore / L1SessionStore / L2MemoryStore / MemoryStore facade —— 三层语义是 OpenCS 差异化核心，无合身 OSS（§6.6 C 类）
- **延迟**：sqlite-vec / Qdrant → v1 向量检索

## 集成边界
- `MemoryStore` 是唯一对外接口；Worker 不直接 import 各层 Store
- L0 / L2 使用同一 SQLite 文件（不同表）；L1 纯内存，不持久化

## 升级与停更预案
- FTS5 → sqlite-vec：只改 L2 的检索实现，接口 `search(query, limit)` 不变
- 切 Qdrant：实现 `QdrantL2Store` 实现同一抽象，MemoryStore 构造时注入
