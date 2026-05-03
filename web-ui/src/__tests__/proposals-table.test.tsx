import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProposalsTable } from "@/components/proposals-table";
import type { ProposalSummary } from "@/lib/types";

const items: ProposalSummary[] = [
  {
    id: "p-1", dimension: "skill", action: "create",
    status: "hitl_pending", risk_level: "medium", confidence: 0.8, trace_id: "t-1",
  },
  {
    id: "p-2", dimension: "memory", action: "update",
    status: "hitl_pending", risk_level: "high", confidence: 0.9, trace_id: null,
  },
];

describe("ProposalsTable", () => {
  it("renders one row per proposal", () => {
    render(<ProposalsTable items={items} onRowClick={vi.fn()} />);
    expect(screen.getByText("p-1")).toBeInTheDocument();
    expect(screen.getByText("p-2")).toBeInTheDocument();
    expect(screen.getByText("skill")).toBeInTheDocument();
  });

  it("calls onRowClick with proposal id when a row is clicked", async () => {
    const userEvent = (await import("@testing-library/user-event")).default;
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<ProposalsTable items={items} onRowClick={onClick} />);
    await user.click(screen.getByText("p-1"));
    expect(onClick).toHaveBeenCalledWith("p-1");
  });

  it("renders empty state when items is empty", () => {
    render(<ProposalsTable items={[]} onRowClick={vi.fn()} />);
    expect(screen.getByText(/no proposals/i)).toBeInTheDocument();
  });
});
