import { z } from "zod";

export const quoteRequestSchema = z.object({
  varyant_id: z.number().int().positive("Varyant seçilmelidir."),
  miktar: z.number().positive("Miktar pozitif olmalıdır."),
});

export type QuoteRequestInput = z.infer<typeof quoteRequestSchema>;
