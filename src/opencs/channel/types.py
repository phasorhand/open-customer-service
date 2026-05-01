from typing import Literal

from pydantic import BaseModel, ConfigDict


class SendResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    delivered: bool
    platform_message_id: str | None = None
    error: str | None = None


class HealthStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["healthy", "degraded", "down"]
    detail: str | None = None


class MediaRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    url: str
    mime: str
    size_bytes: int | None = None


class ChannelConfig(BaseModel):
    """Channel-specific install-time config. Subclassed per adapter."""

    model_config = ConfigDict(extra="allow")

    channel_id: str
