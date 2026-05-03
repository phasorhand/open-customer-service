"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const items = [
  { href: "/", label: "Dashboard" },
  { href: "/proposals", label: "Proposals" },
  { href: "/audit-log", label: "Audit Log" },
  { href: "/replays", label: "Replay" },
  { href: "/crm", label: "CRM Config" },
];

export function SidebarNav() {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-1 p-4">
      {items.map((it) => (
        <Link
          key={it.href}
          href={it.href}
          className={cn(
            "rounded-md px-3 py-2 text-sm hover:bg-muted",
            pathname === it.href && "bg-muted font-medium",
          )}
        >
          {it.label}
        </Link>
      ))}
    </nav>
  );
}
