class L1SessionStore:
    """Ephemeral in-memory session state. Not persisted; cleared on conversation close."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, object]] = {}

    def set(self, conversation_id: str, key: str, value: object) -> None:
        self._sessions.setdefault(conversation_id, {})[key] = value

    def get(self, conversation_id: str, key: str) -> object | None:
        return self._sessions.get(conversation_id, {}).get(key)

    def get_all(self, conversation_id: str) -> dict[str, object]:
        return dict(self._sessions.get(conversation_id, {}))

    def close(self, conversation_id: str) -> None:
        self._sessions.pop(conversation_id, None)
