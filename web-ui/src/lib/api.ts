import type {
  AuditLogListResponse,
  CRMConfig,
  CRMValidateResponse,
  DecisionResponse,
  EvolutionDimension,
  ProposalDetail,
  ProposalListResponse,
  ProposalStatus,
  ReplayMode,
  ReplayResponse,
  StatsResponse,
} from "./types";

const BASE = "/api/admin";

async function request<T>(
  path: string,
  init?: RequestInit & { searchParams?: Record<string, string | number | undefined> },
): Promise<T> {
  let url = `${BASE}${path}`;
  if (init?.searchParams) {
    const sp = new URLSearchParams();
    for (const [k, v] of Object.entries(init.searchParams)) {
      if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
    }
    const qs = sp.toString();
    if (qs) url += `?${qs}`;
  }
  const res = await fetch(url, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listProposals: (params: {
    status?: ProposalStatus;
    dimension?: EvolutionDimension;
    limit?: number;
    offset?: number;
  }) => request<ProposalListResponse>("/proposals", { searchParams: params }),

  getProposal: (id: string) => request<ProposalDetail>(`/proposals/${id}`),

  approveProposal: (id: string, reviewer: string) =>
    request<DecisionResponse>(`/proposals/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ reviewer }),
    }),

  rejectProposal: (id: string, reviewer: string, note: string) =>
    request<DecisionResponse>(`/proposals/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reviewer, note }),
    }),

  listAuditLog: (params: {
    actor?: string;
    decision?: string;
    limit?: number;
    offset?: number;
  }) => request<AuditLogListResponse>("/audit-log", { searchParams: params }),

  getStats: () => request<StatsResponse>("/stats"),

  postReplay: (body: {
    source_conversation_id: string;
    mode: ReplayMode;
    overrides?: Record<string, unknown>;
  }) =>
    request<ReplayResponse>("/replays", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getCRMConfig: () => request<CRMConfig>("/crm/config"),

  putCRMConfig: (body: CRMConfig) =>
    request<CRMConfig>("/crm/config", {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  validateCRM: (body: { base_url: string; schema_json: string }) =>
    request<CRMValidateResponse>("/crm/validate", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
