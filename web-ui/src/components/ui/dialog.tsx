"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

export function Dialog({
  open, onOpenChange, children,
}: { open: boolean; onOpenChange: (o: boolean) => void; children: React.ReactNode }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
         onClick={() => onOpenChange(false)}>
      <div className="max-w-lg w-full rounded-lg bg-background p-6 shadow-lg"
           onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}

export function DialogTitle({ className, ...p }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn("text-lg font-semibold mb-2", className)} {...p} />;
}

export function DialogFooter({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mt-4 flex justify-end gap-2", className)} {...p} />;
}
