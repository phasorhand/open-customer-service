from pydantic import BaseModel, ConfigDict


class ChannelCapabilities(BaseModel):
    """Declared per-adapter feature set; upstream consults it instead of branching on platform."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    supports_text: bool = True
    supports_image: bool = False
    supports_voice: bool = False
    supports_card: bool = False
    supports_proactive_send: bool = False
    supports_history_fetch: bool = False
    max_message_length: int = 2000
    rate_limit_per_minute: int | None = None
