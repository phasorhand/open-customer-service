"use client";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ApprovalDialog } from "@/components/approval-dialog";
import {
  useApproveProposal,
  useProposalDetail,
  useRejectProposal,
} from "@/lib/queries";

export default function ProposalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data, isLoading, isError } = useProposalDetail(id);
  const approve = useApproveProposal();
  const reject = useRejectProposal();
  const [dialog, setDialog] = useState<"approve" | "reject" | null>(null);

  if (isLoading) return <Skeleton className="h-64" />;
  if (isError || !data) return <div className="text-destructive">Failed to load.</div>;

  const langfuseHost = typeof window !== "undefined" ? window.localStorage.getItem("langfuse_host") ?? "" : "";
  const traceUrl = data.trace_id && langfuseHost ? `${langfuseHost}/trace/${data.trace_id}` : null;

  return (
    <div className="space-y-4">
      <Button variant="ghost" onClick={() => router.back()}>&larr; Back</Button>
      <h1 className="text-2xl font-semibold">Proposal {data.id}</h1>

      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>Dimension: <Badge>{data.dimension}</Badge></div>
          <div>Action: <Badge variant="outline">{data.action}</Badge></div>
          <div>Status: <Badge variant="warning">{data.status}</Badge></div>
          <div>Risk: {data.risk_level}</div>
          <div>Confidence: {data.confidence.toFixed(2)}</div>
          {traceUrl && (
            <div>
              Trace: <a className="underline text-blue-600" href={traceUrl} target="_blank">{data.trace_id}</a>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Payload</CardTitle></CardHeader>
        <CardContent>
          <pre className="rounded bg-muted p-3 text-xs overflow-auto">{JSON.stringify(data.payload, null, 2)}</pre>
        </CardContent>
      </Card>

      {data.replay_result && (
        <Card>
          <CardHeader><CardTitle>Replay Verdict</CardTitle></CardHeader>
          <CardContent>
            <pre className="rounded bg-muted p-3 text-xs overflow-auto">{JSON.stringify(data.replay_result, null, 2)}</pre>
          </CardContent>
        </Card>
      )}

      {data.status === "hitl_pending" && (
        <div className="flex gap-2">
          <Button onClick={() => setDialog("approve")}>Approve</Button>
          <Button variant="destructive" onClick={() => setDialog("reject")}>Reject</Button>
        </div>
      )}

      <ApprovalDialog
        mode={dialog ?? "approve"}
        open={dialog !== null}
        proposalId={data.id}
        onClose={() => setDialog(null)}
        onSubmit={async ({ reviewer, note }) => {
          if (dialog === "approve") {
            await approve.mutateAsync({ id: data.id, reviewer });
          } else if (dialog === "reject") {
            await reject.mutateAsync({ id: data.id, reviewer, note });
          }
          setDialog(null);
          router.push("/proposals");
        }}
      />
    </div>
  );
}
