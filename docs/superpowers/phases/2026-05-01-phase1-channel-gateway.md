# Phase 1 Channel Gateway — close note

## Delivered

- `ChannelAdapter` ABC + `ChannelCapabilities` + `ChannelRegistry`
- Unified `InboundMessage` / `OutboundAction` / `ContentPart` schemas
- `ExecutionToken` Protocol + `StubExecutionToken` (Phase-2 will replace impl, not signature)
- `WebChatAdapter` (in-process WS for QA / replay smoke)
- `WecomCustomerServiceAdapter` (parse_inbound + reply send) using `wechatpy` for crypto
- FastAPI gateway: `GET/POST /webhook/wecom_cs`, `WS /ws/webchat`, `GET /health`

## Tests

`uv run pytest -v` — 35 tests passing across `tests/channel/*` and `tests/gateway/*`.

## Quality Gates

- **Ruff**: `All checks passed!`
- **Mypy**: `Success: no issues found in 14 source files`

## Known deferrals (intentional, scheduled by phase)

- `ExecutionToken` real signing/verification → Phase 2 (Harness)
- `add_tag` / `add_to_crm` / `transfer_to_human` outbound kinds → Phase 2/4
- WeCom 会话存档 → out of MVP
- 飞书 / WecomGroupBot adapters → v1 (per spec §5)
- Image / voice content parts plumbed through schema but not yet rendered into WeCom payloads → Phase 2

## Hand-off contract for Phase 2 (Agent Core + Harness)

- Phase 2 supplies `InboundHandler = Callable[[InboundMessage], Awaitable[None]]` to `create_app(...)`
- Phase 2 replaces `StubExecutionToken` with the real signed token; adapter signatures unchanged
- `OutboundAction.metadata` keys consumed by `WecomCustomerServiceAdapter.send`:
  `action_id`, `open_kfid`, `external_userid`
