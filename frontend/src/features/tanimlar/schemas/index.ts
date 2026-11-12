import { z } from "zod";

/** Liste filtreleri (istemci tarafı; API yazma yok). */
export const definitionFilterSchema = z.object({
  q: z.string().optional(),
  sort: z.enum(["kod_asc", "kod_desc", "ad_asc", "ad_desc", "ttl_asc", "ttl_desc"]).optional(),
});

export type DefinitionFilterInput = z.infer<typeof definitionFilterSchema>;
