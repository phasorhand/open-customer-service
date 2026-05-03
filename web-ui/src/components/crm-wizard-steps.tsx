"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { CRMConfig, CRMValidateResponse } from "@/lib/types";

export function CRMWizardSteps({
  onValidate, onSave,
}: {
  onValidate: (body: { base_url: string; schema_json: string }) => Promise<CRMValidateResponse>;
  onSave: (cfg: CRMConfig) => Promise<unknown>;
}) {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [baseUrl, setBaseUrl] = useState("");
  const [schemaJson, setSchemaJson] = useState("");
  const [validation, setValidation] = useState<CRMValidateResponse | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  if (step === 1) {
    return (
      <div className="space-y-3">
        <div>
          <label htmlFor="base_url" className="text-sm font-medium">Base URL</label>
          <Input id="base_url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
        </div>
        <Button disabled={!baseUrl} onClick={() => setStep(2)}>Next</Button>
      </div>
    );
  }
  if (step === 2) {
    return (
      <div className="space-y-3">
        <div>
          <label htmlFor="schema" className="text-sm font-medium">OpenAPI schema (JSON)</label>
          <textarea
            id="schema"
            className="flex min-h-[200px] w-full rounded-md border border-border bg-background px-3 py-2 text-xs font-mono"
            value={schemaJson}
            onChange={(e) => setSchemaJson(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
          <Button
            disabled={!schemaJson}
            onClick={async () => {
              const res = await onValidate({ base_url: baseUrl, schema_json: schemaJson });
              setValidation(res);
              if (res.ok) setStep(3);
            }}
          >
            Validate
          </Button>
        </div>
        {validation && !validation.ok && (
          <div className="text-destructive text-sm">{validation.errors.join("; ")}</div>
        )}
      </div>
    );
  }
  if (step === 3 && validation) {
    return (
      <div className="space-y-3">
        <p className="text-sm">Select operations to expose as tools:</p>
        {validation.detected_operations.map((op) => (
          <label key={op} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={selected.has(op)}
              onChange={(e) => {
                const next = new Set(selected);
                if (e.target.checked) next.add(op); else next.delete(op);
                setSelected(next);
              }}
            />
            {op}
          </label>
        ))}
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setStep(2)}>Back</Button>
          <Button
            onClick={async () => {
              await onSave({
                base_url: baseUrl,
                schema_json: schemaJson,
                exposed_operations: Array.from(selected),
              });
              setStep(4);
            }}
          >
            Save
          </Button>
        </div>
      </div>
    );
  }
  return <div className="text-green-600 font-medium">CRM config saved.</div>;
}
