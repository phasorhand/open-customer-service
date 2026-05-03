from __future__ import annotations

from typing import TYPE_CHECKING

from opencs.evolution.types import Proposal, ProposalAction

if TYPE_CHECKING:
    from opencs.tools.protocol import Tool
    from opencs.tools.registry import ToolRegistry


class CRMToolApplyError(Exception):
    pass


class CRMToolProposalHandler:
    def __init__(self, *, registry: ToolRegistry) -> None:
        self._registry = registry

    def apply(self, proposal: Proposal, *, tool: Tool | None = None) -> None:
        tool_id = proposal.payload.get("tool_id")
        if not tool_id:
            raise CRMToolApplyError("proposal.payload must contain 'tool_id'")

        if proposal.action in (ProposalAction.CREATE, ProposalAction.UPDATE):
            if tool is None:
                raise CRMToolApplyError(
                    "tool instance must be provided for CREATE/UPDATE proposals"
                )
            self._registry.register(tool)

        elif proposal.action == ProposalAction.DEPRECATE:
            self._registry.deregister(str(tool_id))
