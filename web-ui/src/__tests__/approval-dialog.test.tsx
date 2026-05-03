import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApprovalDialog } from "@/components/approval-dialog";

describe("ApprovalDialog", () => {
  it("renders approve form when mode=approve", () => {
    render(
      <ApprovalDialog
        mode="approve" open proposalId="p-1"
        onClose={vi.fn()} onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByText(/approve proposal p-1/i)).toBeInTheDocument();
  });

  it("submits with reviewer when approve", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(
      <ApprovalDialog
        mode="approve" open proposalId="p-1"
        onClose={vi.fn()} onSubmit={onSubmit}
      />,
    );
    await user.type(screen.getByLabelText(/reviewer/i), "alice");
    await user.click(screen.getByRole("button", { name: /confirm/i }));
    expect(onSubmit).toHaveBeenCalledWith({ reviewer: "alice", note: "" });
  });

  it("submits with note when reject", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(
      <ApprovalDialog
        mode="reject" open proposalId="p-2"
        onClose={vi.fn()} onSubmit={onSubmit}
      />,
    );
    await user.type(screen.getByLabelText(/reviewer/i), "bob");
    await user.type(screen.getByLabelText(/note/i), "risky");
    await user.click(screen.getByRole("button", { name: /confirm/i }));
    expect(onSubmit).toHaveBeenCalledWith({ reviewer: "bob", note: "risky" });
  });

  it("disables confirm when reviewer is empty", () => {
    render(
      <ApprovalDialog
        mode="approve" open proposalId="p-1"
        onClose={vi.fn()} onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /confirm/i })).toBeDisabled();
  });
});
