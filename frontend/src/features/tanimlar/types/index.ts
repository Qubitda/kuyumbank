/** GET /api/v1/sales-channels/ — runtime: {count, results, server_now} */

export interface SalesChannel {
  id: number;
  kod: string;
  ad: string;
  quote_ttl_saniye?: number | null;
  /** Liste yalnızca aktif=True döner; alan API’de yoksa true kabul edilir */
  aktif?: boolean;
}

export interface SalesChannelPage {
  count: number;
  results: SalesChannel[];
  server_now?: string;
}

export type DefinitionCategoryId = "sales-channels" | "fiyat-gruplari" | "ayar-milyem" | "kur-metal" | "kur-doviz";

export interface DefinitionCategoryMeta {
  id: DefinitionCategoryId;
  label: string;
  description: string;
  backendModel: string;
  /** OpenAPI / runtime HTTP yüzeyi var mı */
  apiAvailable: boolean;
  endpoint?: string;
}
