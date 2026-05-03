"use client";
import { Badge } from "@/components/ui/badge";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";
import type { ProposalSummary, ProposalStatus } from "@/lib/types";

const STATUS_VARIANT: Record<ProposalStatus, "default" | "outline" | "warning" | "destructive" | "success"> = {
  pending: "outline",
  shadow_running: "outline",
  hitl_pending: "warning",
  auto_promoted: "success",
  hitl_approved: "success",
  rejected: "destructive",
};

export function ProposalsTable({
  items, onRowClick,
}: {
  items: ProposalSummary[];
  onRowClick: (id: string) => void;
}) {
  if (items.length === 0) {
    return <div className="text-muted-foreground text-sm p-8 text-center">No proposals found.</div>;
  }
  return (
    <Table>
      <THead>
        <TR>
          <TH>ID</TH><TH>Dimension</TH><TH>Action</TH><TH>Status</TH><TH>Risk</TH><TH>Confidence</TH>
        </TR>
      </THead>
      <TBody>
        {items.map((p) => (
          <TR key={p.id} onClick={() => onRowClick(p.id)} className="cursor-pointer">
            <TD className="font-mono text-xs">{p.id}</TD>
            <TD>{p.dimension}</TD>
            <TD>{p.action}</TD>
            <TD><Badge variant={STATUS_VARIANT[p.status]}>{p.status}</Badge></TD>
            <TD>{p.risk_level}</TD>
            <TD>{p.confidence.toFixed(2)}</TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}
