import { apiFetch } from "@/lib/api/client";
import type { CariHesap, CreditInfo } from "../types";

export const finansService = {
  getMyFinance(): Promise<CariHesap> {
    return apiFetch<CariHesap>("/finance/me/");
  },
  getMyCredit(): Promise<CreditInfo> {
    return apiFetch<CreditInfo>("/credit/me/");
  },
  getCariList(): Promise<CariHesap[]> {
    return apiFetch<CariHesap[]>("/finance/cari/");
  },
};
