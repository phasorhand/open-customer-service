import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReplayConfigForm } from "@/components/replay-config-form";

describe("ReplayConfigForm", () => {
  it("calls onSubmit with the form values", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<ReplayConfigForm onSubmit={onSubmit} isSubmitting={false} />);
    await user.type(screen.getByLabelText(/conversation id/i), "c-1");
    await user.selectOptions(screen.getByLabelText(/mode/i), "strict");
    await user.click(screen.getByRole("button", { name: /run replay/i }));
    expect(onSubmit).toHaveBeenCalledWith({
      source_conversation_id: "c-1",
      mode: "strict",
      prompt_override: "",
    });
  });

  it("disables submit when conversation id is empty", () => {
    render(<ReplayConfigForm onSubmit={vi.fn()} isSubmitting={false} />);
    expect(screen.getByRole("button", { name: /run replay/i })).toBeDisabled();
  });

  it("disables submit while submitting", async () => {
    const user = userEvent.setup();
    render(<ReplayConfigForm onSubmit={vi.fn()} isSubmitting={true} />);
    await user.type(screen.getByLabelText(/conversation id/i), "c-1");
    expect(screen.getByRole("button", { name: /running/i })).toBeDisabled();
  });
});
