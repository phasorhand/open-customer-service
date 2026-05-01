import pytest

from opencs.channel.adapter import ChannelAdapter
from opencs.channel.capabilities import ChannelCapabilities
from opencs.channel.registry import ChannelRegistry, UnknownChannelError


class _A(ChannelAdapter):
    channel_id = "a"
    capabilities = ChannelCapabilities()

    async def parse_inbound(self, raw_event):  # type: ignore[override]
        raise NotImplementedError

    async def send(self, action, token):  # type: ignore[override]
        raise NotImplementedError

    async def on_install(self, config):  # type: ignore[override]
        return None

    async def health_check(self):  # type: ignore[override]
        raise NotImplementedError


def test_register_and_lookup() -> None:
    r = ChannelRegistry()
    a = _A()
    r.register(a)
    assert r.get("a") is a
    assert "a" in r.ids()


def test_duplicate_register_rejected() -> None:
    r = ChannelRegistry()
    r.register(_A())
    with pytest.raises(ValueError):
        r.register(_A())


def test_unknown_channel_raises() -> None:
    r = ChannelRegistry()
    with pytest.raises(UnknownChannelError):
        r.get("nope")
