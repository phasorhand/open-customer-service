"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogFooter, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export function ApprovalDialog({
  mode, open, proposalId, onClose, onSubmit,
}: {
  mode: "approve" | "reject";
  open: boolean;
  proposalId: string;
  onClose: () => void;
  onSubmit: (v: { reviewer: string; note: string }) => void;
}) {
  const [reviewer, setReviewer] = useState("");
  const [note, setNote] = useState("");
  const title = mode === "approve"
    ? `Approve proposal ${proposalId}`
    : `Reject proposal ${proposalId}`;
  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogTitle>{title}</DialogTitle>
      <div className="space-y-3">
        <div>
          <label htmlFor="reviewer" className="text-sm font-medium">Reviewer</label>
          <Input id="reviewer" value={reviewer} onChange={(e) => setReviewer(e.target.value)} />
        </div>
        {mode === "reject" && (
          <div>
            <label htmlFor="note" className="text-sm font-medium">Note</label>
            <Input id="note" value={note} onChange={(e) => setNote(e.target.value)} />
          </div>
        )}
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button
          disabled={!reviewer}
          variant={mode === "reject" ? "destructive" : "default"}
          onClick={() => onSubmit({ reviewer, note })}
        >
          Confirm
        </Button>
      </DialogFooter>
    </Dialog>
  );
}
