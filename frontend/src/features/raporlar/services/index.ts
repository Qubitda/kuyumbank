import { apiFetch } from "@/lib/api/client";
import type {
  BuyerBehaviorReport,
  CommercialOrderReport,
  RevenueAnomalyReport,
} from "../types";

export const raporlarService = {
  getCommercialOrders(params?: {
    date_from?: string;
    date_to?: string;
  }): Promise<CommercialOrderReport> {
    const q = new URLSearchParams();
    if (params?.date_from) q.set("date_from", params.date_from);
    if (params?.date_to) q.set("date_to", params.date_to);
    const query = q.toString() ? `?${q}` : "";
    return apiFetch<CommercialOrderReport>(`/reports/orders/${query}`);
  },
  getBuyerBehavior(params?: {
    date_from?: string;
    date_to?: string;
  }): Promise<BuyerBehaviorReport> {
    const q = new URLSearchParams();
    if (params?.date_from) q.set("date_from", params.date_from);
    if (params?.date_to) q.set("date_to", params.date_to);
    const query = q.toString() ? `?${q}` : "";
    return apiFetch<BuyerBehaviorReport>(`/reports/buyer-behavior/${query}`);
  },
  getRevenueAnomalies(esikCiro: string): Promise<RevenueAnomalyReport> {
    return apiFetch<RevenueAnomalyReport>(
      `/ops/anomalies/ciro/?esik_ciro=${encodeURIComponent(esikCiro)}`
    );
  },
};
