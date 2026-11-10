import { z } from "zod";

/** Form şemaları — alanlar OpenAPI ile doldurulur. */
export const siparisFormStubSchema = z.object({
  _stub: z.literal(true).optional(),
});
