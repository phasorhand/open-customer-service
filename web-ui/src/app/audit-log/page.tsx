"use client";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { AuditLogTable } from "@/components/audit-log-table";
import { useAuditLog } from "@/lib/queries";

export default function AuditLogPage() {
  const [actor, setActor] = useState("");
  const [offset, setOffset] = useState(0);
  const { data, isLoading } = useAuditLog({
    actor: actor || undefined, limit: 50, offset,
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Audit Log</h1>
      <div className="flex gap-2">
        <Input
          placeholder="Filter by actor"
          value={actor}
          onChange={(e) => { setActor(e.target.value); setOffset(0); }}
        />
      </div>
      {isLoading && <Skeleton className="h-64" />}
      {data && (
        <>
          <AuditLogTable items={data.items} />
          <div className="flex justify-between">
            <Button variant="outline" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 50))}>
              Previous
            </Button>
            <div className="text-sm text-muted-foreground">
              {offset + 1}–{offset + data.items.length} of {data.total}
            </div>
            <Button variant="outline" disabled={offset + 50 >= data.total} onClick={() => setOffset(offset + 50)}>
              Next
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
