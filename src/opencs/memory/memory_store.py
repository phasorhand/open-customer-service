from opencs.channel.schema import InboundMessage
from opencs.memory.l0_store import L0Event, L0RawEventStore
from opencs.memory.l1_store import L1SessionStore
from opencs.memory.l2_store import L2MemoryStore, MemoryEntry


class MemoryStore:
    """Facade for all three memory layers. The only memory interface Workers/Orchestrator use."""

    def __init__(
        self,
        l0_db: str = ":memory:",
        l2_db: str = ":memory:",
    ) -> None:
        self.l0 = L0RawEventStore(db_path=l0_db)
        self.l1 = L1SessionStore()
        self.l2 = L2MemoryStore(db_path=l2_db)

    def record_inbound(self, message: InboundMessage) -> None:
        self.l0.append(L0Event(
            conversation_id=message.conversation_id,
            kind="inbound_message",
            payload={"text": message.text_concat(), "customer_id": message.customer_id},
            ts=message.timestamp,
        ))
        turn_count = int(self.l1.get(message.conversation_id, "turn_count") or 0)
        self.l1.set(message.conversation_id, "turn_count", turn_count + 1)

    def load_context(
        self,
        conversation_id: str,
        *,
        customer_id: str,
        message_text: str,
    ) -> dict[str, object]:
        turn_count = int(self.l1.get(conversation_id, "turn_count") or 0)

        subject_entries = self.l2.get_by_subject(f"customer:{customer_id}")
        fts_entries = self.l2.search(message_text, limit=3) if message_text.strip() else []

        seen: set[str] = set()
        combined: list[str] = []
        for entry in subject_entries + fts_entries:
            if entry.version_id not in seen:
                seen.add(entry.version_id)
                combined.append(entry.body)

        l2_summary: str | None = "\n---\n".join(combined) if combined else None

        return {
            "turn_count": turn_count,
            "l2_summary": l2_summary,
            "customer_id": customer_id,
        }

    def write_l2(self, *, subject_id: str, kind: str, body: str) -> str:
        return self.l2.write(MemoryEntry(subject_id=subject_id, kind=kind, body=body))
