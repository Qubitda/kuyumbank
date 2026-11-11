import { apiFetch } from "@/lib/api/client";
import type { SalesChannel } from "../types";

export const tanimlarService = {
  getSalesChannels(): Promise<SalesChannel[]> {
    return apiFetch<SalesChannel[]>("/sales-channels/");
  },
};
