import { z } from "zod";

export const stockAdjustmentSchema = z.object({
  varyant_id: z.number().int().positive("Varyant seçilmelidir."),
  miktar: z.string().min(1, "Miktar girilmelidir."),
  aciklama: z.string().optional(),
});

export type StockAdjustmentInput = z.infer<typeof stockAdjustmentSchema>;
