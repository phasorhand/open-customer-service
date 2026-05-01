# OpenCS · Core Schema · OSS 调研

## 目标

提供跨渠道统一的消息数据模型（ContentPart、InboundMessage），支持多媒体内容、时区感知、平台原始载荷透传。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| [Pydantic v2](https://github.com/pydantic/pydantic) | MIT | 2026-04 | 20.3k | ~3MB | ✅ | 业界标准数据验证，模型冻结、模型验证器、类型联合完全满足需求 |
| [dataclasses + cattrs](https://github.com/python-attrs/cattrs) | MIT | 2026-01 | 2.1k | ~400KB | ⚠️ | 功能足够但需额外包装，Pydantic 一体化验证更强 |
| [Marshmallow](https://github.com/marshmallow-code/marshmallow) | MIT | 2026-02 | 6.8k | ~800KB | ⚠️ | 功能齐全但 API 层次深，Pydantic v2 更简洁 |

## 决策

**复用**：`Pydantic @ v2.x`（已在 pyproject.toml 中）

### 理由

- OpenCS 主体是 Python 服务，Pydantic v2 是事实标准
- 原生支持模型冻结（ContentPart 不可变）、模型验证器（校验时区感知）、类型联合（SenderKind）
- 无需额外包装：直接继承 BaseModel，接口清晰
- 依赖已引入，不增加 footprint

### 排除的候选

- dataclasses + cattrs：需额外生态，学习成本高，Pydantic 社区活跃
- Marshmallow：功能等同，序列化 API 复杂，Pydantic 设计更现代

## 集成边界

- **ContentPart**：冻结 BaseModel，公开的 kind / text / media_url / mime / extra 字段
- **InboundMessage**：BaseModel（非冻结），暴露 text_concat() 方法；raw_payload、platform_meta 作为透传容器
- Pydantic 验证错误直接抛给上层处理，不做二次包装

## 升级与停更预案

- Pydantic v2 维护活跃，最新版本 v2.10.x（2026-04）
- 监控：`pip index versions pydantic` 每半年
- 停更预案：迁移至 attrs + cattrs，但短期内无此风险
