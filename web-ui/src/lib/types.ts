// Mirror of src/opencs/gateway/admin_schemas.py (hand-maintained).
// When admin_schemas.py changes, update this file.

export type EvolutionDimension = "skill" | "memory" | "crm_tool";
export type ProposalAction = "create" | "update" | "deprecate";
export type ProposalStatus =
  | "pending"
  | "shadow_running"
  | "hitl_pending"
  | "auto_promoted"
  | "hitl_approved"
  | "rejected";
export type GateDecision = "auto_promote" | "hitl_pending" | "rejected";

export interface ProposalSummary {
  id: string;
  dimension: EvolutionDimension;
  action: ProposalAction;
  status: ProposalStatus;
  risk_level: string;
  confidence: number;
  trace_id: string | null;
}

export interface ProposalListResponse {
  items: ProposalSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProposalDetail {
  id: string;
  dimension: EvolutionDimension;
  action: ProposalAction;
  status: ProposalStatus;
  risk_level: string;
  confidence: number;
  payload: Record<string, unknown>;
  evidence: Record<string, unknown>;
  replay_result: Record<string, unknown> | null;
  gate_decision: GateDecision | null;
  reviewer: string | null;
  rejection_note: string | null;
  trace_id: string | null;
}

export interface DecisionResponse {
  id: string;
  status: ProposalStatus;
  reviewer: string | null;
  rejection_note: string | null;
}

export interface AuditLogEntry {
  action_id: string;
  tool_id: string;
  risk_tier: number;
  decision: string;
  actor: string;
  ts: string;
  note: string | null;
}

export interface AuditLogListResponse {
  items: AuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface StatsResponse {
  pending_proposals: number;
  approved_today: number;
  rejected_today: number;
  recent_audit: AuditLogEntry[];
}

export interface CRMConfig {
  base_url: string;
  schema_json: string;
  exposed_operations: string[];
}

export interface CRMValidateResponse {
  ok: boolean;
  detected_operations: string[];
  errors: string[];
}

export type ReplayMode = "strict" | "partial" | "what_if";

export interface ReplayResponse {
  session_id: string;
  verdict: string;
  divergence_count: number;
  baseline_event_count: number;
  replay_event_count: number;
}
