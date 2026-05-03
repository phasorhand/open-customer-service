"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ProposalsTable } from "@/components/proposals-table";
import { useProposalsList } from "@/lib/queries";
import type { EvolutionDimension, ProposalStatus } from "@/lib/types";

export default function ProposalsPage() {
  const router = useRouter();
  const [status, setStatus] = useState<ProposalStatus | "">("hitl_pending");
  const [dimension, setDimension] = useState<EvolutionDimension | "">("");
  const { data, isLoading, isError } = useProposalsList({
    status: status || undefined,
    dimension: dimension || undefined,
    limit: 50,
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Proposals</h1>
      <div className="flex gap-2">
        <Select value={status} onChange={(e) => setStatus(e.target.value as ProposalStatus | "")}>
          <option value="">All statuses</option>
          <option value="hitl_pending">HITL Pending</option>
          <option value="auto_promoted">Auto-promoted</option>
          <option value="hitl_approved">HITL Approved</option>
          <option value="rejected">Rejected</option>
        </Select>
        <Select value={dimension} onChange={(e) => setDimension(e.target.value as EvolutionDimension | "")}>
          <option value="">All dimensions</option>
          <option value="skill">Skill</option>
          <option value="memory">Memory</option>
          <option value="crm_tool">CRM Tool</option>
        </Select>
      </div>
      {isLoading && <Skeleton className="h-64" />}
      {isError && <div className="text-destructive">Failed to load proposals.</div>}
      {data && (
        <ProposalsTable
          items={data.items}
          onRowClick={(id) => router.push(`/proposals/${id}`)}
        />
      )}
    </div>
  );
}
