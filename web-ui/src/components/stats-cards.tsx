"use client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useStats } from "@/lib/queries";

export function StatsCards() {
  const { data, isLoading, isError } = useStats();
  if (isLoading) {
    return (
      <div className="grid grid-cols-3 gap-4">
        <Skeleton className="h-24" /><Skeleton className="h-24" /><Skeleton className="h-24" />
      </div>
    );
  }
  if (isError || !data) {
    return <div className="text-destructive">Failed to load stats.</div>;
  }
  return (
    <div className="grid grid-cols-3 gap-4">
      <Card>
        <CardHeader><CardTitle>Pending proposals</CardTitle></CardHeader>
        <CardContent><div className="text-3xl font-semibold">{data.pending_proposals}</div></CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Approved today</CardTitle></CardHeader>
        <CardContent><div className="text-3xl font-semibold">{data.approved_today}</div></CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Rejected today</CardTitle></CardHeader>
        <CardContent><div className="text-3xl font-semibold">{data.rejected_today}</div></CardContent>
      </Card>
    </div>
  );
}
