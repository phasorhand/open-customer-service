"use client";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import type { AuditLogEntry } from "@/lib/types";

export function AuditLogTable({ items }: { items: AuditLogEntry[] }) {
  if (items.length === 0) {
    return <div className="text-muted-foreground text-sm p-8 text-center">No audit entries.</div>;
  }
  return (
    <Table>
      <THead>
        <TR>
          <TH>Timestamp</TH><TH>Actor</TH><TH>Decision</TH><TH>Action ID</TH><TH>Tool</TH><TH>Note</TH>
        </TR>
      </THead>
      <TBody>
        {items.map((e, idx) => (
          <TR key={`${e.action_id}-${idx}`}>
            <TD className="font-mono text-xs">{new Date(e.ts).toLocaleString()}</TD>
            <TD>{e.actor}</TD>
            <TD>{e.decision}</TD>
            <TD className="font-mono text-xs">{e.action_id}</TD>
            <TD>{e.tool_id}</TD>
            <TD className="text-xs">{e.note ?? ""}</TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}
