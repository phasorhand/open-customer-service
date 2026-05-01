from collections.abc import Iterable

from opencs.channel.adapter import ChannelAdapter


class UnknownChannelError(KeyError):
    """Raised when no adapter is registered for a given channel_id."""


class ChannelRegistry:
    """Single source of truth for live ChannelAdapter instances."""

    def __init__(self) -> None:
        self._by_id: dict[str, ChannelAdapter] = {}

    def register(self, adapter: ChannelAdapter) -> None:
        if adapter.channel_id in self._by_id:
            raise ValueError(f"channel_id already registered: {adapter.channel_id!r}")
        self._by_id[adapter.channel_id] = adapter

    def get(self, channel_id: str) -> ChannelAdapter:
        try:
            return self._by_id[channel_id]
        except KeyError as e:
            raise UnknownChannelError(channel_id) from e

    def ids(self) -> Iterable[str]:
        return self._by_id.keys()
