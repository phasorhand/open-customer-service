# Channel Gateway · OSS 调研

## 目标
统一接入 IM 平台（企微客服、WebChat、未来飞书/Slack），把平台原生事件翻译成统一 `InboundMessage`，把 `OutboundAction` 翻译成原生 API；提供 `ChannelAdapter` 抽象供 Gateway 唯一依赖。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| [wechatpy/wechatpy](https://github.com/wechatpy/wechatpy) | MIT | 2025-12 | 4.2k | ~600KB | ✅ 复用 | 企微/公众号回调加解密、签名校验、token 管理；社区活跃 |
| [Errbot/errbot](https://github.com/errbot/errbot) | GPL-3.0 | 2025-08 | 3.1k | — | ❌ | License 否决（GPL 传染） |
| [microsoft/botbuilder-python](https://github.com/microsoft/botbuilder-python) | MIT | 2024-09 | 730 | 大 | ❌ 借抽象 | 抽象过重、强绑 Azure，但 Activity schema 思路可借 |
| [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | LGPL-3.0 | 2026-03 | 26k | — | ⚠️ v2 | 仅 Telegram；MVP 不需要，v2 通道阶段再评估 |

## 决策
- **复用**：`wechatpy @ ^1.8` —— 仅取其 `WeChatCrypto`（回调加解密 / 签名校验）与 `WeChatClient` 的 access_token 管理；不依赖其 webhook 路由层（与 FastAPI 不契合）
- **借抽象**：botbuilder 的 `Activity` schema 思路 → 我们自己的 `InboundMessage`/`OutboundAction`（更窄、字段更明确）
- **自建**：`ChannelAdapter` ABC + `ChannelRegistry`——抽象是产品差异化的一部分，且过于轻量（< 200 行）不值得引外部库

## 集成边界
- `wechatpy` 仅在 `wecom_cs.py` 内使用，封装为内部 helper；不暴露给 adapter ABC
- 所有跨平台接口只经过 `schema.py` / `adapter.py` 定义的类型；upstream 代码不能 `import wechatpy`

## 升级与停更预案
- wechatpy 若停更：crypto 算法稳定（AES + SHA1），可直接 fork 内联 ~300 行；token 管理改用 `httpx` 自实现
- 监控：`pyproject.toml` pin minor，依赖更新走 dependabot 周报
