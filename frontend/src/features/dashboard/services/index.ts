import { apiFetch, fetchMeDashboard, unwrapResults } from "@/lib/api/client";
import type { Capabilities, MeDashboard } from "@/lib/api/types";
import { siparisService } from "@/features/siparis";
import { firmalarService } from "@/features/firmalar";
import { finansService } from "@/features/finans";
import { stokService } from "@/features/stok";
import { lojistikService } from "@/features/lojistik";
import type { OpsShipment } from "@/features/lojistik";
import { urunlerService } from "@/features/urunler";
import { raporlarService } from "@/features/raporlar";
import type {
  DashboardFilters,
  DashboardSnapshot,
  DashboardSlice,
  OpsOrderSummary,
} from "../types";

function emptySnapshot(): DashboardSnapshot {
  return {
    meDashboard: null,
    orders: [],
    ordersCount: null,
    approvals: [],
    approvalsCount: null,
    cari: [],
    credit: null,
    ledger: [],
    stock: [],
    stockCount: null,
    shipments: [],
    shipmentsCount: null,
    catalogCount: null,
    commercialReport: null,
    behaviorReport: null,
    opsSummary: null,
    errors: {},
  };
}

function errMsg(reason: unknown): string {
  return reason instanceof Error ? reason.message : "İstek başarısız.";
}

function settleError(
  errors: DashboardSnapshot["errors"],
  slice: DashboardSlice,
  result: PromiseSettledResult<unknown>
) {
  if (result.status === "rejected") {
    errors[slice] = errMsg(result.reason);
  }
}

export const dashboardService = {
  getMeDashboard(): Promise<MeDashboard> {
    return fetchMeDashboard();
  },

  getOpsOrderSummary(): Promise<OpsOrderSummary> {
    return apiFetch<OpsOrderSummary>("/ops/orders/summary/");
  },

  async loadSnapshot(
    caps: Capabilities | null | undefined,
    filters: DashboardFilters
  ): Promise<DashboardSnapshot> {
    const snap = emptySnapshot();
    const c = caps || ({} as Capabilities);

    const reportParams = {
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
    };

    const tasks: Array<Promise<void>> = [];

    tasks.push(
      (async () => {
        const r = await Promise.allSettled([dashboardService.getMeDashboard()]);
        settleError(snap.errors, "meDashboard", r[0]);
        if (r[0].status === "fulfilled") snap.meDashboard = r[0].value;
      })()
    );

    if (c.can_view_orders || c.can_view_cart || c.can_checkout) {
      tasks.push(
        (async () => {
          const r = await Promise.allSettled([
            siparisService.getOrders({ page_size: "20" }),
          ]);
          settleError(snap.errors, "orders", r[0]);
          if (r[0].status === "fulfilled") {
            snap.orders = unwrapResults(r[0].value);
            snap.ordersCount =
              typeof r[0].value.count === "number" ? r[0].value.count : snap.orders.length;
          }
        })()
      );
    }

    if (c.can_approve) {
      tasks.push(
        (async () => {
          const r = await Promise.allSettled([firmalarService.getApprovals()]);
          settleError(snap.errors, "approvals", r[0]);
          if (r[0].status === "fulfilled") {
            snap.approvals = unwrapResults(r[0].value);
            snap.approvalsCount =
              typeof r[0].value.count === "number"
                ? r[0].value.count
                : snap.approvals.length;
          }
        })()
      );
    }

    if (c.can_view_finance || c.can_view_credit) {
      tasks.push(
        (async () => {
          const jobs: Array<PromiseSettledResult<unknown>> = [];
          if (c.can_view_credit) {
            const creditRes = await Promise.allSettled([finansService.getMyCredit()]);
            jobs.push(creditRes[0]);
            if (creditRes[0].status === "fulfilled") snap.credit = creditRes[0].value;
          }
          if (c.can_view_finance) {
            const finRes = await Promise.allSettled([
              finansService.getCariList(),
              finansService.getLedger({ page_size: "10" }),
            ]);
            jobs.push(...finRes);
            if (finRes[0].status === "fulfilled") {
              snap.cari = unwrapResults(finRes[0].value);
            }
            if (finRes[1].status === "fulfilled") {
              snap.ledger = unwrapResults(finRes[1].value);
            }
          }
          const fails = jobs.filter((j) => j.status === "rejected");
          if (fails.length === jobs.length && fails.length > 0) {
            snap.errors.finance = errMsg(
              (fails[0] as PromiseRejectedResult).reason
            );
          }
        })()
      );
    }

    if (c.can_view_supplier_stock) {
      tasks.push(
        (async () => {
          const r = await Promise.allSettled([
            stokService.getSupplierStock({ page_size: "50" }),
          ]);
          settleError(snap.errors, "stock", r[0]);
          if (r[0].status === "fulfilled") {
            snap.stock = unwrapResults(r[0].value);
            snap.stockCount =
              typeof r[0].value.count === "number" ? r[0].value.count : snap.stock.length;
          }
        })()
      );
    }

    if (c.can_view_shipments || c.can_manage_shipment) {
      tasks.push(
        (async () => {
          const primary = c.can_manage_shipment
            ? lojistikService.getShipments()
            : lojistikService.getBuyerShipments();
          const r = await Promise.allSettled([primary]);
          settleError(snap.errors, "shipments", r[0]);
          if (r[0].status === "fulfilled") {
            const raw = r[0].value as {
              count?: number;
              results?: Array<{
                id: number;
                durum: string;
                order_id?: number;
                allowed_actions?: string[];
              }>;
            };
            const rows = raw.results ?? [];
            snap.shipments = rows.map(
              (s): OpsShipment => ({
                id: s.id,
                order_id: s.order_id ?? 0,
                durum: s.durum,
                allowed_actions: s.allowed_actions || [],
              })
            );
            snap.shipmentsCount =
              typeof raw.count === "number" ? raw.count : snap.shipments.length;
          }
        })()
      );
    }

    if (c.can_view_catalog) {
      tasks.push(
        (async () => {
          const r = await Promise.allSettled([
            urunlerService.getCatalog({ page_size: "1" }),
          ]);
          settleError(snap.errors, "catalog", r[0]);
          if (r[0].status === "fulfilled") {
            snap.catalogCount =
              typeof r[0].value.count === "number" ? r[0].value.count : null;
          }
        })()
      );
    }

    // Raporlar: capability yok; 403 olursa sessizce hata kaydı
    tasks.push(
      (async () => {
        const r = await Promise.allSettled([
          raporlarService.getCommercialOrders(reportParams),
          raporlarService.getBuyerBehavior(reportParams),
        ]);
        if (r[0].status === "fulfilled") snap.commercialReport = r[0].value;
        if (r[1].status === "fulfilled") snap.behaviorReport = r[1].value;
        if (r[0].status === "rejected" && r[1].status === "rejected") {
          snap.errors.reports = errMsg(
            (r[0] as PromiseRejectedResult).reason
          );
        }
      })()
    );

    if (c.can_view_ops) {
      tasks.push(
        (async () => {
          const r = await Promise.allSettled([
            dashboardService.getOpsOrderSummary(),
          ]);
          settleError(snap.errors, "opsSummary", r[0]);
          if (r[0].status === "fulfilled") snap.opsSummary = r[0].value;
        })()
      );
    }

    await Promise.all(tasks);
    return snap;
  },
};
