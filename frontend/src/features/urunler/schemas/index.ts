import { z } from "zod";

export const catalogFilterSchema = z.object({
  q: z.string().optional(),
  kategori: z.string().optional(),
  ayar: z.string().optional(),
});

export type CatalogFilterInput = z.infer<typeof catalogFilterSchema>;
