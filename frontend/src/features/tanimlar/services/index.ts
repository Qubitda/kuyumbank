import { apiFetch } from "@/lib/api/client";
import type { SalesChannel, SalesChannelPage } from "../types";

function normalizeSalesChannelPage(
  data: SalesChannelPage | SalesChannel[] | null | undefined
): SalesChannelPage {
  if (!data) return { count: 0, results: [] };
  if (Array.isArray(data)) {
    return { count: data.length, results: data };
  }
  const results = Array.isArray(data.results) ? data.results : [];
  return {
    count: typeof data.count === "number" ? data.count : results.length,
    results,
    server_now: data.server_now,
  };
}

export const tanimlarService = {
  /** Sayfalı / sarmalanmış yanıt (yönetim ekranı). */
  async getSalesChannelsPage(): Promise<SalesChannelPage> {
    const data = await apiFetch<SalesChannelPage | SalesChannel[]>("/sales-channels/");
    return normalizeSalesChannelPage(data);
  },

  /**
   * Dizi olarak aktif satış kanalları.
   * Quote/catalog gibi tüketiciler için geriye dönük dizi API’si.
   */
  async getSalesChannels(): Promise<SalesChannel[]> {
    const page = await this.getSalesChannelsPage();
    return page.results;
  },

  listSalesChannels(): Promise<SalesChannel[]> {
    return this.getSalesChannels();
  },
};
