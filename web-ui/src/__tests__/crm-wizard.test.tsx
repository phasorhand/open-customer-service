import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CRMWizardSteps } from "@/components/crm-wizard-steps";

describe("CRMWizardSteps", () => {
  it("shows step 1 (base URL) first", () => {
    render(<CRMWizardSteps onValidate={vi.fn()} onSave={vi.fn()} />);
    expect(screen.getByLabelText(/base url/i)).toBeInTheDocument();
  });

  it("advances to step 2 when base URL entered and Next clicked", async () => {
    const user = userEvent.setup();
    render(<CRMWizardSteps onValidate={vi.fn()} onSave={vi.fn()} />);
    await user.type(screen.getByLabelText(/base url/i), "https://crm.example.com");
    await user.click(screen.getByRole("button", { name: /next/i }));
    expect(screen.getByLabelText(/openapi schema/i)).toBeInTheDocument();
  });

  it("calls onValidate with schema when Validate clicked", async () => {
    const user = userEvent.setup();
    const onValidate = vi.fn().mockResolvedValue({
      ok: true, detected_operations: ["getCustomer"], errors: [],
    });
    render(<CRMWizardSteps onValidate={onValidate} onSave={vi.fn()} />);
    await user.type(screen.getByLabelText(/base url/i), "https://crm.example.com");
    await user.click(screen.getByRole("button", { name: /next/i }));
    const textarea = screen.getByLabelText(/openapi schema/i);
    // fireEvent.change avoids userEvent keyboard parsing of "{" as modifier
    const { fireEvent } = await import("@testing-library/react");
    fireEvent.change(textarea, { target: { value: '{"paths":{}}' } });
    await user.click(screen.getByRole("button", { name: /validate/i }));
    expect(onValidate).toHaveBeenCalledWith({
      base_url: "https://crm.example.com",
      schema_json: '{"paths":{}}',
    });
  });
});
