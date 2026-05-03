"use client";
import { CRMWizardSteps } from "@/components/crm-wizard-steps";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCRMConfig, usePutCRMConfig, useValidateCRM } from "@/lib/queries";

export default function CRMPage() {
  const { data: current } = useCRMConfig();
  const put = usePutCRMConfig();
  const validate = useValidateCRM();

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">CRM Configuration</h1>
      {current && (
        <Card>
          <CardHeader><CardTitle>Current</CardTitle></CardHeader>
          <CardContent>
            <div>Base URL: {current.base_url}</div>
            <div>Exposed: {current.exposed_operations.join(", ") || "—"}</div>
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader><CardTitle>{current ? "Update" : "Configure"}</CardTitle></CardHeader>
        <CardContent>
          <CRMWizardSteps
            onValidate={(body) => validate.mutateAsync(body)}
            onSave={(cfg) => put.mutateAsync(cfg)}
          />
        </CardContent>
      </Card>
    </div>
  );
}
