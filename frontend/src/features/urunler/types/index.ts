/**
 * OpenAPI katalog + ops ürün tipleri.
 * Kör havuz: alıcıda tedarikçi/maliyet yok; fiyat quote ile gelir.
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

export interface OpsProductVariant {
  id: number;
  sku: string;
  aktif: boolean;
  gram?: string | null;
  renk_id?: number | null;
  beden_id?: number | null;
  ek_bedel?: string;
}

export interface OpsProduct {
  id: number;
  ad: string;
  platform_kodu: string;
  aciklama?: string;
  kategori_id: number;
  kategori?: string;
  ayar_id: number;
  ayar?: string;
  fiyat_tipi?: string;
  onay_durumu: string;
  yayin_durumu: string;
  red_nedeni?: string;
  olusturan_firma_id: number;
  varyant_count: number;
  allowed_actions?: string[];
  varyantlar?: OpsProductVariant[];
}

export interface OpsProductPage {
  count: number;
  page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: OpsProduct[];
}

export interface OpsProductCreateRequest {
  ad: string;
  kategori_id: number;
  ayar_id: number;
  aciklama?: string;
  fiyat_tipi?: string;
  satis_kanali_id?: number;
}

export interface OpsProductVariantCreateRequest {
  gram?: string;
  renk_id?: number;
  ek_bedel?: string;
}
