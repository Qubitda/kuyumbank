import { apiFetch, newIdempotencyKey } from "@/lib/api/client";
import type { BuyerPriceLock, BuyerQuote } from "@/lib/api/types";
import type {
  BuyerRfqCreateRequest,
  PriceLock,
  PriceQuote,
  SupplierOffer,
  SupplierOfferCreateRequest,
  SupplierOfferPage,
  SupplierRfq,
  SupplierRfqPage,
} from "../types";

function mapQuote(q: BuyerQuote): PriceQuote {
  return {
    id: q.id,
    varyant_id: q.varyant_id ?? 0,
    birim_fiyat: q.gram_basi_vergisiz || q.toplam_vergisiz,
    para_birimi: q.para_birimi,
    expires_at: q.expires_at || undefined,
    allowed_actions: q.allowed_actions,
    durum: q.durum,
    gram: q.gram,
    gram_basi_vergisiz: q.gram_basi_vergisiz,
    toplam_vergisiz: q.toplam_vergisiz,
    varyant_sku: q.varyant_sku,
    urun: q.urun,
  };
}

function mapLock(l: BuyerPriceLock): PriceLock {
  return {
    id: l.id,
    quote_id: l.quote_id,
    kilit_fiyati: l.toplam_vergisiz || "",
    para_birimi: l.para_birimi || "TRY",
    durum: (l.durum as PriceLock["durum"]) || "AKTIF",
    expires_at: l.expires_at || "",
    gecerli: l.gecerli,
  };
}

export const fiyatlamaService = {
  /** Liste GET yok (OpenAPI). Tek kayıt: GET /quotes/{id}/ */
  getQuote(id: number | string): Promise<PriceQuote> {
    return apiFetch<BuyerQuote>(`/quotes/${id}/`).then(mapQuote);
  },
  createQuote(data: {
    varyant_id: number;
    satis_kanali_id: number;
    para_birimi?: string;
  }): Promise<PriceQuote> {
    return apiFetch<BuyerQuote>("/quotes/", {
      method: "POST",
      body: {
        varyant_id: data.varyant_id,
        satis_kanali_id: data.satis_kanali_id,
        para_birimi: data.para_birimi || "TRY",
      },
      idempotencyKey: newIdempotencyKey(),
    }).then(mapQuote);
  },
  getPriceLock(id: number | string): Promise<PriceLock> {
    return apiFetch<BuyerPriceLock>(`/price-locks/${id}/`).then(mapLock);
  },
  createPriceLock(quoteId: number): Promise<PriceLock> {
    return apiFetch<BuyerPriceLock>("/price-locks/", {
      method: "POST",
      body: { quote_id: quoteId },
      idempotencyKey: newIdempotencyKey(),
    }).then(mapLock);
  },
  getSupplierRfqs(): Promise<SupplierRfqPage> {
    return apiFetch<SupplierRfqPage>("/supplier/rfqs/");
  },
  getSupplierRfq(id: number | string): Promise<SupplierRfq> {
    return apiFetch<SupplierRfq>(`/supplier/rfqs/${id}/`);
  },
  getSupplierOffers(): Promise<SupplierOfferPage> {
    return apiFetch<SupplierOfferPage>("/supplier/offers/");
  },
  createSupplierOffer(data: SupplierOfferCreateRequest): Promise<SupplierOffer> {
    return apiFetch<SupplierOffer>("/supplier/offers/", {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  submitSupplierOffer(id: number | string): Promise<SupplierOffer> {
    return apiFetch<SupplierOffer>(`/supplier/offers/${id}/submit/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  deactivateSupplierOffer(id: number | string): Promise<SupplierOffer> {
    return apiFetch<SupplierOffer>(`/supplier/offers/${id}/deactivate/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  getBuyerRfqs(): Promise<SupplierRfqPage> {
    return apiFetch<SupplierRfqPage>("/rfqs/");
  },
  getBuyerRfqDetail(id: number | string): Promise<SupplierRfq> {
    return apiFetch<SupplierRfq>(`/rfqs/${id}/`);
  },
  createBuyerRfq(data: BuyerRfqCreateRequest): Promise<SupplierRfq> {
    return apiFetch<SupplierRfq>("/rfqs/", {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  sendBuyerRfq(id: number | string): Promise<SupplierRfq> {
    return apiFetch<SupplierRfq>(`/rfqs/${id}/send/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
};
