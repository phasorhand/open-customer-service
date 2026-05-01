from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from opencs.channel.schema import InboundMessage
from opencs.harness.action_plan import ActionPlan


@dataclass
class WorkerInput:
    """Everything a Worker needs to produce ActionPlans."""
    message: InboundMessage
    session_context: dict[str, object] = field(default_factory=dict)


class BaseWorker(ABC):
    """Base class for all Worker agents.

    Workers are pure computation: given a WorkerInput, produce ActionPlans.
    They must not call ToolProvider, ChannelAdapter, or Harness directly.
    """

    worker_id: str

    @abstractmethod
    async def run(self, inp: WorkerInput) -> list[ActionPlan]:
        """Process the input and return zero or more ActionPlans."""
