import * as React from "react";
import { cn } from "@/lib/utils";

const variants: Record<string, string> = {
  default: "bg-primary text-primary-foreground",
  outline: "border border-border",
  warning: "bg-yellow-100 text-yellow-900",
  destructive: "bg-destructive text-destructive-foreground",
  success: "bg-green-100 text-green-900",
};

export function Badge({
  className, variant = "default", ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof variants }) {
  return <span className={cn("inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold", variants[variant], className)} {...props} />;
}
