from opencs.channel.capabilities import ChannelCapabilities


def test_defaults() -> None:
    c = ChannelCapabilities()
    assert c.supports_text is True
    assert c.supports_image is False
    assert c.max_message_length == 2000
    assert c.rate_limit_per_minute is None


def test_immutable() -> None:
    c = ChannelCapabilities()
    try:
        c.supports_text = False  # type: ignore[misc]
    except (AttributeError, TypeError, ValueError):
        return
    raise AssertionError("ChannelCapabilities should be frozen")
