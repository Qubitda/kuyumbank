/**
 * OpenAPI normatif katalog tipleri (API_CONTRACT ve ADR-0005/0029).
 * Kör havuz kuralı: Tedarikçi kimliği ve maliyet alanları alıcı arayüzünde ASLA bulunmaz.
 */

export interface BuyerCatalogVariant {
  id: number;
  sku: string;
  beden: string;
  renk: string;
  gram: string | null;
}

export interface BuyerCatalogItem {
  id: number;
  ad: string;
  platform_kodu: string;
  kategori: string;
  ayar: string;
  varyant_count: number;
  fiyat_tipi: string;
  yayin_durumu: string;
  allowed_actions: string[];
}

export interface BuyerCatalogDetail {
  id: number;
  ad: string;
  platform_kodu: string;
  kategori: string;
  ayar: string;
  aciklama?: string;
  fiyat_tipi: string;
  allowed_actions: string[];
  varyantlar: BuyerCatalogVariant[];
}

export interface BuyerCatalogPage {
  count: number;
  page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: BuyerCatalogItem[];
}
