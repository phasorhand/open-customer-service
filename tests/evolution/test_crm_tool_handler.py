import pytest

from opencs.evolution.handlers.crm_tool import CRMToolApplyError, CRMToolProposalHandler
from opencs.evolution.types import EvolutionDimension, Proposal, ProposalAction
from opencs.tools.protocol import ToolDescription, ToolResult
from opencs.tools.registry import ToolRegistry


class _FakeCRMTool:
    def __init__(self, tid: str = "crm.get_order") -> None:
        self.tool_id = tid

    def describe(self) -> ToolDescription:
        return ToolDescription(
            tool_id=self.tool_id, name=self.tool_id,
            description="", parameters={}, read_only=True,
        )

    async def call(self, args, token) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={})

    async def dry_run(self, args) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={"_dry_run": True})

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry()


@pytest.fixture
def handler(registry: ToolRegistry) -> CRMToolProposalHandler:
    return CRMToolProposalHandler(registry=registry)


def _create_proposal(tool_id: str = "crm.get_order") -> Proposal:
    return Proposal(
        id="prop-crm-1",
        dimension=EvolutionDimension.CRM_TOOL,
        action=ProposalAction.CREATE,
        payload={"tool_id": tool_id},
        confidence=0.88,
        risk_level="low",
    )


def _deprecate_proposal(tool_id: str = "crm.get_order") -> Proposal:
    return Proposal(
        id="prop-crm-2",
        dimension=EvolutionDimension.CRM_TOOL,
        action=ProposalAction.DEPRECATE,
        payload={"tool_id": tool_id},
        confidence=0.88,
        risk_level="low",
    )


def test_create_registers_tool(handler: CRMToolProposalHandler, registry: ToolRegistry) -> None:
    tool = _FakeCRMTool()
    handler.apply(_create_proposal(), tool=tool)
    assert registry.get("crm.get_order") is tool


def test_update_re_registers_tool(handler: CRMToolProposalHandler, registry: ToolRegistry) -> None:
    old_tool = _FakeCRMTool()
    new_tool = _FakeCRMTool()
    handler.apply(_create_proposal(), tool=old_tool)
    update_proposal = Proposal(
        id="prop-crm-upd",
        dimension=EvolutionDimension.CRM_TOOL,
        action=ProposalAction.UPDATE,
        payload={"tool_id": "crm.get_order"},
        confidence=0.88,
        risk_level="low",
    )
    handler.apply(update_proposal, tool=new_tool)
    assert registry.get("crm.get_order") is new_tool


def test_deprecate_removes_tool(handler: CRMToolProposalHandler, registry: ToolRegistry) -> None:
    tool = _FakeCRMTool()
    handler.apply(_create_proposal(), tool=tool)
    handler.apply(_deprecate_proposal())
    with pytest.raises(KeyError):
        registry.get("crm.get_order")


def test_deprecate_is_idempotent_when_not_registered(handler: CRMToolProposalHandler) -> None:
    handler.apply(_deprecate_proposal())


def test_create_without_tool_raises(handler: CRMToolProposalHandler) -> None:
    with pytest.raises(CRMToolApplyError, match="tool"):
        handler.apply(_create_proposal(), tool=None)


def test_missing_tool_id_raises(handler: CRMToolProposalHandler) -> None:
    bad = Proposal(
        id="prop-bad",
        dimension=EvolutionDimension.CRM_TOOL,
        action=ProposalAction.CREATE,
        payload={},
        confidence=0.8,
        risk_level="low",
    )
    with pytest.raises(CRMToolApplyError, match="tool_id"):
        handler.apply(bad, tool=_FakeCRMTool())


def test_registry_deregister() -> None:
    reg = ToolRegistry()
    tool = _FakeCRMTool()
    reg.register(tool)
    assert reg.get("crm.get_order") is tool
    reg.deregister("crm.get_order")
    with pytest.raises(KeyError):
        reg.get("crm.get_order")


def test_registry_deregister_idempotent() -> None:
    reg = ToolRegistry()
    reg.deregister("crm.nonexistent")
