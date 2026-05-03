# tracing · OSS 调研

## 目标
为 OpenCS 的 orchestrator + LLM 调用链路提供 trace 能力；把 trace_id 绑定到 Evolution Proposal 上，支持 admin UI 深链到原始对话。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| langfuse/langfuse-python | MIT | 2026-04 | 2.1k | ~18MB | ✅ | 与 spec §6.6 锁定的自托管 Langfuse 服务端配套；官方 SDK |
| openllmetry (traceloop) | Apache-2.0 | 2026-03 | 4.5k | ~30MB | ❌ | 绑定 OpenTelemetry 后端，自托管需额外部署 Jaeger/Tempo；与 spec 不匹配 |
| phoenix (Arize) | Elastic-2.0 | 2026-04 | 3.8k | ~60MB | ❌ | Elastic license 不兼容商业自托管；体量超载 |

## 决策
- **复用**: `langfuse @ ^2.50` (Python SDK)
- 封装在 `src/opencs/tracing/langfuse_client.py`，暴露 `init_langfuse()` / `observe` / `get_current_trace_id()` 抽象
- 自定义封装原因：让上层只依赖 OpenCS 的抽象；未来切换到 OpenTelemetry 时只改 adapter

## 集成边界
- orchestrator.handle() 用 `@observe(name="conversation.handle")` 装饰
- 每个 LLM chat 调用在 LiteLLMClient 里用 Langfuse 的 litellm 集成自动追踪
- EvolutionGate.evaluate() 读取 `get_current_trace_id()` 并写入 Proposal

## 升级与停更预案
- 监控 langfuse/langfuse-python releases（GitHub）
- 如 > 18 月停更或 license 变更，替换为 OpenTelemetry + opencs-tracing 自实现（接口保持不变）
