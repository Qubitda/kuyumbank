import { z } from "zod";

/** Form şemaları — alanlar OpenAPI ile doldurulur. */
export const firmalarFormStubSchema = z.object({
  _stub: z.literal(true).optional(),
});
