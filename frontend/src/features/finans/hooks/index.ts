"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { unwrapResults } from "@/lib/api/client";
import { finansService } from "../services";

export const finansKeys = {
  all: ["finans"] as const,
  me: (pb = "TRY") => [...finansKeys.all, "me", pb] as const,
  credit: (pb = "TRY") => [...finansKeys.all, "credit", pb] as const,
  cari: () => [...finansKeys.all, "cari"] as const,
  ledger: () => [...finansKeys.all, "ledger"] as const,
  ops: () => [...finansKeys.all, "ops"] as const,
};

export function useFinanceMeQuery(paraBirimi = "TRY", enabled = true) {
  return useQuery({
    queryKey: finansKeys.me(paraBirimi),
    queryFn: () => finansService.getMyFinance(paraBirimi),
    enabled,
  });
}

export function useCreditQuery(paraBirimi = "TRY", enabled = true) {
  return useQuery({
    queryKey: finansKeys.credit(paraBirimi),
    queryFn: () => finansService.getMyCredit(paraBirimi),
    enabled,
  });
}

export function useCariListQuery(enabled = true) {
  return useQuery({
    queryKey: finansKeys.cari(),
    queryFn: async () => unwrapResults(await finansService.getCariList()),
    enabled,
  });
}

export function useLedgerQuery(enabled = true) {
  return useQuery({
    queryKey: finansKeys.ledger(),
    queryFn: async () => unwrapResults(await finansService.getLedger()),
    enabled,
  });
}

export function useOpsFinanceQuery(enabled = false) {
  return useQuery({
    queryKey: finansKeys.ops(),
    queryFn: () => finansService.getOpsFinance(),
    enabled,
  });
}

export function useCreatePaymentIntentMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (orderId: number) => finansService.createPaymentIntent(orderId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: finansKeys.all });
    },
  });
}
