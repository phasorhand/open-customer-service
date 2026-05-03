from __future__ import annotations

from dataclasses import dataclass, field

from opencs.memory.l0_store import L0Event, L0RawEventStore


@dataclass
class Trace:
    conversation_id: str
    events: list[L0Event] = field(default_factory=list)
    inbound_messages: list[L0Event] = field(default_factory=list)
    llm_cache: dict[str, str] = field(default_factory=dict)
    tool_cache: dict[str, dict[str, object]] = field(default_factory=dict)


class TraceLoader:
    def __init__(self, *, l0: L0RawEventStore) -> None:
        self._l0 = l0

    def load(self, conversation_id: str) -> Trace:
        events = self._l0.list(conversation_id=conversation_id)
        trace = Trace(conversation_id=conversation_id, events=events)

        for event in events:
            if event.kind == "inbound_message":
                trace.inbound_messages.append(event)
            elif event.kind == "llm_call":
                recording_id = event.payload.get("recording_id")
                output = event.payload.get("output")
                if recording_id and output:
                    trace.llm_cache[str(recording_id)] = str(output)
            elif event.kind == "tool_result":
                action_id = event.payload.get("action_id")
                if action_id:
                    trace.tool_cache[str(action_id)] = {
                        "success": event.payload.get("success"),
                        "data": event.payload.get("data"),
                        "error": event.payload.get("error"),
                    }

        return trace
