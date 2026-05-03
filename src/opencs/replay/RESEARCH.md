# replay · OSS 调研

## 目标
构建 Replay Engine：给定一条线上 trace + 一组修复 overrides，重放验证 badcase 是否消失、是否引入 regression。支持 Strict / Partial / WhatIf 三种模式。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| promptfoo | MIT | 2026-04 | 5.2k | ~30MB | ❌ | 评估框架，不支持 trace-level replay 或 tool/memory 重放；概念不匹配 |
| DeepEval | Apache-2.0 | 2026-04 | 4.8k | ~15MB | ❌ | 测试框架，侧重 LLM 输出评分；无 trace replay / tool cache / diff 引擎 |
| LangSmith replay | 商业 SaaS | — | — | — | ❌ | 非 OSS；License 否决 |
| Langfuse datasets | MIT | 2026-04 | 6.1k | — | ⚠️ | dataset 可存 trace 但无重放引擎；用作 trace 存储底座（v1），不用作 replay 逻辑 |

## 决策
- **自建**：Replay Engine（ReplayingLLMClient + ReplayingToolProvider + ReplayDiffer + ReplayEngine）
  - 理由：没有成熟 OSS 做"trace-level what-if replay with tool/memory override + structured diff"——这是 OpenCS 的核心差异化（修复验证闭环）
  - promptfoo / DeepEval 是评估/测试框架，概念层面不同（它们测单条 prompt 质量，我们重放整个 conversation 决策链）
  - OSS 等价物保留为 `DeepEval`——v1 引入作为 verdict 自动评估后端
- **复用**：无额外依赖；L0RawEventStore 已满足 trace 存储需求；LLMClient / ToolExecutor 接口已统一

## 集成边界
- `ReplayEngine` 是唯一对外入口：`replay(session: ReplaySession) -> ReplayResult`
- `TraceLoader` 只读 L0；不写任何数据
- `ReplayingLLMClient` 满足 `LLMClient` Protocol
- `ReplayingToolProvider` 包装 `ToolExecutor`，同接口
- `ReplayDiffer` 纯函数：两组 L0Event → DivergencePoint[] + Verdict

## 升级与停更预案
- 自建模块：无外部依赖风险
- v1 引入 DeepEval 作为 verdict 自动评估后端时，Differ 仍保留作为结构化 diff 层（DeepEval 不替代 diff，只替代人工判定）
