import { apiFetch, unwrapResults } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type { BuyerOrder } from "@/features/siparis/types";
import type { DocumentItem } from "../types";

interface ShipmentLike {
  id: number;
  durum: string;
  order_id?: number;
  server_now?: string;
  belgeler_ref?: string;
  pod_ref?: string;
  allowed_actions?: string[];
}

interface LedgerLike {
  id: number;
  referans_tip?: string;
  referans_id?: number | null;
  olusturma_tarihi?: string | null;
  tutar?: string;
  para_birimi?: string;
}

function isHttpUrl(value?: string): value is string {
  if (!value) return false;
  return /^https?:\/\//i.test(value.trim());
}

function pushShipmentDocs(
  items: DocumentItem[],
  list: ShipmentLike[],
  source: DocumentItem["referans_tipi"]
) {
  for (const s of list) {
    const ref = (s.belgeler_ref || s.pod_ref || "").trim();
    items.push({
      id: `${source}-${s.id}`,
      belge_tipi: "SEVKIYAT",
      ad: ref
        ? `Sevkiyat #${s.id} belgesi`
        : `Sevkiyat #${s.id} (${s.durum})`,
      dosya_url: isHttpUrl(ref) ? ref.trim() : undefined,
      referans_tipi: source,
      referans_id: s.id,
      olusturma_tarihi: s.server_now,
      raw_ref: ref || undefined,
    });
  }
}

/**
 * Belge arşivi: sözleşmedeki sevkiyat / sipariş / ledger uçlarından derlenir.
 * Sahte /belgeler/ endpoint kullanılmaz.
 */
export const belgelerService = {
  async getDocuments(): Promise<DocumentItem[]> {
    const items: DocumentItem[] = [];

    const [buyerShip, opsShip, orders, ledger] = await Promise.allSettled([
      apiFetch<Paginated<ShipmentLike>>("/shipments/"),
      apiFetch<Paginated<ShipmentLike>>("/ops/shipments/"),
      apiFetch<Paginated<BuyerOrder>>("/orders/"),
      apiFetch<Paginated<LedgerLike>>("/finance/ledger/"),
    ]);

    if (buyerShip.status === "fulfilled") {
      pushShipmentDocs(items, unwrapResults(buyerShip.value), "shipment");
    }
    if (opsShip.status === "fulfilled") {
      pushShipmentDocs(items, unwrapResults(opsShip.value), "ops_shipment");
    }
    if (orders.status === "fulfilled") {
      for (const o of unwrapResults(orders.value)) {
        items.push({
          id: `order-${o.id}`,
          belge_tipi: "SIPARIS",
          ad: `Sipariş #${o.id} (${o.durum})`,
          referans_tipi: "order",
          referans_id: o.id,
          olusturma_tarihi: o.olusturma_tarihi,
        });
      }
    }
    if (ledger.status === "fulfilled") {
      for (const row of unwrapResults(ledger.value)) {
        if (!row.referans_tip && !row.referans_id) continue;
        items.push({
          id: `ledger-${row.id}`,
          belge_tipi: row.referans_tip || "LEDGER",
          ad: `Ledger #${row.id}${row.referans_id ? ` · ref ${row.referans_id}` : ""}`,
          referans_tipi: "ledger",
          referans_id: row.id,
          olusturma_tarihi: row.olusturma_tarihi || undefined,
          raw_ref:
            row.referans_tip && row.referans_id
              ? `${row.referans_tip}:${row.referans_id}`
              : undefined,
        });
      }
    }

    return items;
  },
};
