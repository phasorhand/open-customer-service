"use client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ReplayResponse } from "@/lib/types";

const VERDICT_VARIANT: Record<string, "success" | "destructive" | "warning" | "outline"> = {
  badcase_fixed: "success",
  badcase_remains: "warning",
  new_regression: "destructive",
  inconclusive: "outline",
};

export function ReplayResultCard({ result }: { result: ReplayResponse }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Result: {result.session_id}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div>
          Verdict: <Badge variant={VERDICT_VARIANT[result.verdict] ?? "outline"}>{result.verdict}</Badge>
        </div>
        <div>Divergences: {result.divergence_count}</div>
        <div>Baseline events: {result.baseline_event_count}</div>
        <div>Replay events: {result.replay_event_count}</div>
      </CardContent>
    </Card>
  );
}
