"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

export interface ReplayFormValues {
  source_conversation_id: string;
  mode: "strict" | "partial" | "what_if";
  prompt_override: string;
}

export function ReplayConfigForm({
  onSubmit, isSubmitting,
}: {
  onSubmit: (v: ReplayFormValues) => void;
  isSubmitting: boolean;
}) {
  const [conv, setConv] = useState("");
  const [mode, setMode] = useState<"strict" | "partial" | "what_if">("what_if");
  const [prompt, setPrompt] = useState("");

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ source_conversation_id: conv, mode, prompt_override: prompt });
      }}
    >
      <div>
        <label htmlFor="conv" className="text-sm font-medium">Conversation ID</label>
        <Input id="conv" value={conv} onChange={(e) => setConv(e.target.value)} />
      </div>
      <div>
        <label htmlFor="mode" className="text-sm font-medium">Mode</label>
        <Select id="mode" value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
          <option value="what_if">what_if</option>
          <option value="strict">strict</option>
          <option value="partial">partial</option>
        </Select>
      </div>
      <div>
        <label htmlFor="prompt" className="text-sm font-medium">Prompt override (optional)</label>
        <Input id="prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
      </div>
      <Button type="submit" disabled={!conv || isSubmitting}>
        {isSubmitting ? "Running…" : "Run replay"}
      </Button>
    </form>
  );
}
