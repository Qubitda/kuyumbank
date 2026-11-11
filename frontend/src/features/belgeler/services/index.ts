import { apiFetch } from "@/lib/api/client";
import type { DocumentItem } from "../types";

export const belgelerService = {
  getDocuments(params?: Record<string, string>): Promise<DocumentItem[]> {
    const query = params ? `?${new URLSearchParams(params).toString()}` : "";
    return apiFetch<DocumentItem[]>(`/belgeler/${query}`);
  },
};
