from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ContentKind = Literal["text", "image", "voice", "file", "card"]
SenderKind = Literal["customer", "agent_human", "system"]


class ContentPart(BaseModel):
    """Atomic message segment. Multimodal messages are lists of parts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: ContentKind
    text: str | None = None
    media_url: str | None = None
    mime: str | None = None
    extra: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_kind_fields(self) -> "ContentPart":
        if self.kind == "text" and not self.text:
            raise ValueError("text part requires non-empty text")
        if self.kind in {"image", "voice", "file"} and not self.media_url:
            raise ValueError(f"{self.kind} part requires media_url")
        return self


class InboundMessage(BaseModel):
    """Platform-neutral inbound message produced by ChannelAdapter.parse_inbound."""

    model_config = ConfigDict(extra="forbid")

    channel_id: str
    conversation_id: str
    customer_id: str
    sender_kind: SenderKind
    content: list[ContentPart]
    timestamp: datetime
    raw_payload: dict[str, object]
    platform_meta: dict[str, object]

    @model_validator(mode="after")
    def _require_aware_timestamp(self) -> "InboundMessage":
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return self

    def text_concat(self) -> str:
        return "\n".join(p.text or "" for p in self.content if p.kind == "text" and p.text)


OutboundKind = Literal["reply", "add_tag", "add_to_crm", "transfer_to_human"]


class OutboundAction(BaseModel):
    """Platform-neutral outbound action consumed by ChannelAdapter.send."""

    model_config = ConfigDict(extra="forbid")

    conversation_id: str
    kind: OutboundKind
    content: list[ContentPart] | None
    target: str | None
    metadata: dict[str, object]

    @model_validator(mode="after")
    def _require_kind_specific_fields(self) -> "OutboundAction":
        if self.kind == "reply" and not self.content:
            raise ValueError("reply action requires non-empty content")
        if self.kind in {"add_tag", "add_to_crm"} and not self.target:
            raise ValueError(f"{self.kind} action requires target")
        return self
