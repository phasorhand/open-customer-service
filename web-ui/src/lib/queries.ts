import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
} from "@tanstack/react-query";
import { api } from "./api";
import type { EvolutionDimension, ProposalStatus } from "./types";

export function useProposalsList(params: {
  status?: ProposalStatus;
  dimension?: EvolutionDimension;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["proposals", params],
    queryFn: () => api.listProposals(params),
  });
}

export function useProposalDetail(id: string) {
  return useQuery({
    queryKey: ["proposal", id],
    queryFn: () => api.getProposal(id),
    enabled: Boolean(id),
  });
}

export function useApproveProposal(): UseMutationResult<
  Awaited<ReturnType<typeof api.approveProposal>>,
  Error,
  { id: string; reviewer: string }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reviewer }) => api.approveProposal(id, reviewer),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["proposals"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

export function useRejectProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reviewer, note }: { id: string; reviewer: string; note: string }) =>
      api.rejectProposal(id, reviewer, note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["proposals"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

export function useAuditLog(params: { actor?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["audit-log", params],
    queryFn: () => api.listAuditLog(params),
  });
}

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: () => api.getStats(),
    refetchInterval: 10_000,
  });
}

export function usePostReplay() {
  return useMutation({
    mutationFn: api.postReplay,
  });
}

export function useCRMConfig() {
  return useQuery({
    queryKey: ["crm-config"],
    queryFn: async () => {
      try {
        return await api.getCRMConfig();
      } catch {
        return null;
      }
    },
  });
}

export function usePutCRMConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.putCRMConfig,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["crm-config"] }),
  });
}

export function useValidateCRM() {
  return useMutation({
    mutationFn: api.validateCRM,
  });
}
