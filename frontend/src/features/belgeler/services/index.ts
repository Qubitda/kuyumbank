import {
  apiFetch,
  newIdempotencyKey,
  unwrapResults,
} from "@/lib/api/client";
import type { Capabilities, Paginated } from "@/lib/api/types";
import type { BuyerOrder } from "@/features/siparis/types";
import type {
  DocumentItem,
  DocumentsSnapshot,
  DocumentSource,
  PodAttachRequest,
} from "../types";

interface ShipmentRow {
  id: number;
  durum: string;
  order_id?: number;
  server_now?: string;
  allowed_actions?: string[];
  tasiyici?: string;
  takip_no?: string;
  pod?: {
    teslim_alan?: string;
    olusturma_tarihi?: string | null;
    belgeler_ref?: string;
  } | null;
  belgeler_ref?: string;
  pod_ref?: string;
}

interface LedgerRow {
  id: number;
  referans_tip?: string;
  referans_id?: number | null;
  olusturma_tarihi?: string | null;
  tutar?: string;
  para_birimi?: string;
  hareket_tipi?: string;
  yon?: string;
}

interface ReturnRow {
  id: number;
  durum: string;
  order_id?: number;
  server_now?: string;
  allowed_actions?: string[];
  sebep?: string;
}

interface InspectionRow {
  id: number;
  durum: string;
  order_id?: number;
  order_line_id?: number;
  olusturma_tarihi?: string | null;
  notlar?: string;
  allowed_actions?: string[];
}

function isHttpUrl(value?: string): value is string {
  if (!value) return false;
  return /^https?:\/\//i.test(value.trim());
}

function guessFormat(ref?: string): string | undefined {
  if (!ref) return undefined;
  const clean = ref.split("?")[0].toLowerCase();
  if (clean.endsWith(".pdf")) return "PDF";
  if (/\.(png|jpe?g|gif|webp)$/.test(clean)) return "IMAGE";
  if (/\.(txt|csv|json)$/.test(clean)) return "TEXT";
  if (isHttpUrl(ref)) return "URL";
  return "REF";
}

function errMsg(reason: unknown): string {
  return reason instanceof Error ? reason.message : "İstek başarısız.";
}

function shipmentDocs(
  list: ShipmentRow[],
  source: Extract<DocumentSource, "shipment" | "ops_shipment">
): DocumentItem[] {
  const out: DocumentItem[] = [];
  for (const s of list) {
    const podRef = (s.pod?.belgeler_ref || s.belgeler_ref || s.pod_ref || "").trim();
    const href = source === "ops_shipment" ? "/lojistik" : "/lojistik";

    out.push({
      id: `${source}-${s.id}`,
      belge_tipi: "SEVKIYAT",
      ad: `Sevkiyat #${s.id}`,
      belge_no: `SHP-${s.id}`,
      durum: s.durum,
      referans_tipi: source,
      referans_id: s.id,
      related_order_id: s.order_id,
      olusturma_tarihi: s.server_now,
      raw_ref: s.takip_no || undefined,
      format: "KAYIT",
      allowed_actions: s.allowed_actions,
      href,
      meta: {
        order_id: s.order_id,
        tasiyici: s.tasiyici,
        takip_no: s.takip_no,
      },
    });

    if (s.pod || podRef) {
      out.push({
        id: `${source}-pod-${s.id}`,
        belge_tipi: "POD",
        ad: `POD · Sevkiyat #${s.id}`,
        belge_no: `POD-${s.id}`,
        durum: s.pod ? "KAYITLI" : "REF",
        dosya_url: isHttpUrl(podRef) ? podRef : undefined,
        raw_ref: podRef || undefined,
        referans_tipi: source,
        referans_id: s.id,
        related_order_id: s.order_id,
        olusturma_tarihi: s.pod?.olusturma_tarihi || s.server_now,
        format: guessFormat(podRef) || "REF",
        href,
        meta: {
          teslim_alan: s.pod?.teslim_alan,
          belgeler_ref: podRef,
        },
      });
    }
  }
  return out;
}

export const belgelerService = {
  async getDocuments(caps?: Capabilities | null): Promise<DocumentsSnapshot> {
    const c = caps || ({} as Capabilities);
    const items: DocumentItem[] = [];
    const errors: DocumentsSnapshot["errors"] = {};

    const jobs: Array<Promise<void>> = [];

    if (c.can_view_shipments || c.can_manage_shipment) {
      jobs.push(
        (async () => {
          const r = await Promise.allSettled([
            apiFetch<Paginated<ShipmentRow>>("/shipments/"),
          ]);
          if (r[0].status === "fulfilled") {
            items.push(...shipmentDocs(unwrapResults(r[0].value), "shipment"));
          } else {
            errors.shipment = errMsg(r[0].reason);
          }
        })()
      );
    }

    if (c.can_manage_shipment || c.can_view_ops) {
      jobs.push(
        (async () => {
          const r = await Promise.allSettled([
            apiFetch<Paginated<ShipmentRow>>("/ops/shipments/"),
          ]);
          if (r[0].status === "fulfilled") {
            items.push(...shipmentDocs(unwrapResults(r[0].value), "ops_shipment"));
          } else {
            errors.ops_shipment = errMsg(r[0].reason);
          }
        })()
      );
    }

    if (c.can_view_orders || c.can_view_cart || c.can_checkout) {
      jobs.push(
        (async () => {
          const r = await Promise.allSettled([
            apiFetch<Paginated<BuyerOrder>>("/orders/?page_size=50"),
          ]);
          if (r[0].status === "fulfilled") {
            for (const o of unwrapResults(r[0].value)) {
              items.push({
                id: `order-${o.id}`,
                belge_tipi: "SIPARIS",
                ad: `Sipariş #${o.id}`,
                belge_no: `ORD-${o.id}`,
                durum: o.durum,
                referans_tipi: "order",
                referans_id: o.id,
                related_order_id: o.id,
                olusturma_tarihi: o.olusturma_tarihi,
                format: "KAYIT",
                href: "/siparis",
                meta: { line_count: o.line_count },
              });
            }
          } else {
            errors.order = errMsg(r[0].reason);
          }
        })()
      );
    }

    if (c.can_view_finance) {
      jobs.push(
        (async () => {
          const r = await Promise.allSettled([
            apiFetch<Paginated<LedgerRow>>("/finance/ledger/?page_size=50"),
          ]);
          if (r[0].status === "fulfilled") {
            for (const row of unwrapResults(r[0].value)) {
              items.push({
                id: `ledger-${row.id}`,
                belge_tipi: "LEDGER",
                ad: `Ledger #${row.id}`,
                belge_no: `LED-${row.id}`,
                durum: row.hareket_tipi || row.yon || "KAYIT",
                referans_tipi: "ledger",
                referans_id: row.id,
                related_order_id:
                  row.referans_tip === "order" || row.referans_tip === "ORDER"
                    ? row.referans_id
                    : null,
                olusturma_tarihi: row.olusturma_tarihi || undefined,
                format: "KAYIT",
                href: "/finans",
                raw_ref:
                  row.referans_tip && row.referans_id != null
                    ? `${row.referans_tip}:${row.referans_id}`
                    : undefined,
                meta: {
                  tutar: row.tutar,
                  para_birimi: row.para_birimi,
                  referans_tip: row.referans_tip,
                  referans_id: row.referans_id,
                },
              });
            }
          } else {
            errors.ledger = errMsg(r[0].reason);
          }
        })()
      );
    }

    if (c.can_manage_return || c.can_view_orders) {
      jobs.push(
        (async () => {
          const r = await Promise.allSettled([
            apiFetch<Paginated<ReturnRow>>("/returns/"),
          ]);
          if (r[0].status === "fulfilled") {
            for (const row of unwrapResults(r[0].value)) {
              items.push({
                id: `return-${row.id}`,
                belge_tipi: "IADE",
                ad: `İade #${row.id}`,
                belge_no: `RET-${row.id}`,
                durum: row.durum,
                referans_tipi: "return",
                referans_id: row.id,
                related_order_id: row.order_id,
                olusturma_tarihi: row.server_now,
                format: "KAYIT",
                href: "/lojistik",
                allowed_actions: row.allowed_actions,
                meta: { sebep: row.sebep, order_id: row.order_id },
              });
            }
          } else {
            errors.return = errMsg(r[0].reason);
          }
        })()
      );
    }

    if (c.can_manage_qc || c.can_view_ops) {
      jobs.push(
        (async () => {
          const r = await Promise.allSettled([
            apiFetch<Paginated<InspectionRow>>("/ops/inspections/"),
          ]);
          if (r[0].status === "fulfilled") {
            for (const row of unwrapResults(r[0].value)) {
              items.push({
                id: `insp-${row.id}`,
                belge_tipi: "KALITE",
                ad: `QC İnceleme #${row.id}`,
                belge_no: `QC-${row.id}`,
                durum: row.durum,
                referans_tipi: "inspection",
                referans_id: row.id,
                related_order_id: row.order_id,
                olusturma_tarihi: row.olusturma_tarihi || undefined,
                format: "KAYIT",
                href: "/kalite",
                allowed_actions: row.allowed_actions,
                meta: {
                  order_line_id: row.order_line_id,
                  notlar: row.notlar,
                },
              });
            }
          } else {
            errors.inspection = errMsg(r[0].reason);
          }
        })()
      );
    }

    await Promise.all(jobs);

    items.sort((a, b) => {
      const ta = a.olusturma_tarihi ? Date.parse(a.olusturma_tarihi) : 0;
      const tb = b.olusturma_tarihi ? Date.parse(b.olusturma_tarihi) : 0;
      return tb - ta;
    });

    return { items, errors };
  },

  /** Ops sevkiyat listesi — POD eklenebilir kayıtlar için. */
  listOpsShipments(): Promise<Paginated<ShipmentRow>> {
    return apiFetch<Paginated<ShipmentRow>>("/ops/shipments/");
  },

  submitPod(data: PodAttachRequest): Promise<ShipmentRow> {
    return apiFetch<ShipmentRow>(`/ops/shipments/${data.shipment_id}/pod/`, {
      method: "POST",
      body: {
        teslim_alan: data.teslim_alan,
        notlar: data.notlar || "",
        belgeler_ref: data.belgeler_ref || "",
      },
      idempotencyKey: newIdempotencyKey(),
    });
  },

  async downloadUrl(url: string, filename = "belge"): Promise<void> {
    const res = await fetch(url, {
      credentials: url.startsWith("/") || url.includes(window.location.host)
        ? "include"
        : "omit",
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`İndirme başarısız (HTTP ${res.status}).`);
    }
    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = filename;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objectUrl);
  },
};
