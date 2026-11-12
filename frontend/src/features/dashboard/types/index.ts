import type { MeDashboard } from "@/lib/api/types";
import type { BuyerOrder } from "@/features/siparis/types";
import type { Approval } from "@/features/firmalar/types";
import type { CariHesap, CreditInfo, LedgerEntry } from "@/features/finans/types";
import type { StockBalance } from "@/features/stok/types";
import type { OpsShipment } from "@/features/lojistik/types";
import type {
  CommercialOrderReport,
  BuyerBehaviorReport,
} from "@/features/raporlar/types";

export type DashboardLoadState = "idle" | "loading" | "ready" | "error";

export interface OpsOrderSummary {
  counts?: Record<string, number | string>;
  server_now?: string;
}

export interface DashboardSnapshot {
  meDashboard: MeDashboard | null;
  orders: BuyerOrder[];
  ordersCount: number | null;
  approvals: Approval[];
  approvalsCount: number | null;
  cari: CariHesap[];
  credit: CreditInfo | null;
  ledger: LedgerEntry[];
  stock: StockBalance[];
  stockCount: number | null;
  shipments: OpsShipment[];
  shipmentsCount: number | null;
  catalogCount: number | null;
  commercialReport: CommercialOrderReport | null;
  behaviorReport: BuyerBehaviorReport | null;
  opsSummary: OpsOrderSummary | null;
  errors: Partial<Record<DashboardSlice, string>>;
}

export type DashboardSlice =
  | "meDashboard"
  | "orders"
  | "approvals"
  | "finance"
  | "stock"
  | "shipments"
  | "catalog"
  | "reports"
  | "opsSummary";

export type DatePreset = "7d" | "30d" | "90d" | "custom";

export interface DashboardFilters {
  datePreset: DatePreset;
  dateFrom: string;
  dateTo: string;
  orderDurum: string;
}
