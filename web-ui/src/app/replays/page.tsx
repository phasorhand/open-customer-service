"use client";
import { useState } from "react";
import { ReplayConfigForm, type ReplayFormValues } from "@/components/replay-config-form";
import { ReplayResultCard } from "@/components/replay-result-card";
import { usePostReplay } from "@/lib/queries";
import type { ReplayResponse } from "@/lib/types";

export default function ReplaysPage() {
  const [result, setResult] = useState<ReplayResponse | null>(null);
  const mut = usePostReplay();

  async function handleSubmit(v: ReplayFormValues) {
    const overrides = v.prompt_override ? { prompt_override: v.prompt_override } : undefined;
    const res = await mut.mutateAsync({
      source_conversation_id: v.source_conversation_id,
      mode: v.mode,
      overrides,
    });
    setResult(res);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Badcase Replay</h1>
      <ReplayConfigForm onSubmit={handleSubmit} isSubmitting={mut.isPending} />
      {mut.isError && <div className="text-destructive">Replay failed: {String(mut.error)}</div>}
      {result && <ReplayResultCard result={result} />}
    </div>
  );
}
