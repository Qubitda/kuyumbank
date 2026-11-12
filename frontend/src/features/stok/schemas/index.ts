import { z } from "zod";

export const stockAdjustmentSchema = z.object({
  warehouse_id: z.number().int().positive("Depo (warehouse_id) zorunlu."),
  teklif_id: z.number().int().positive("Teklif id zorunlu."),
  miktar: z.string().min(1, "Miktar girilmelidir."),
  neden: z.string().optional(),
});

export type StockAdjustmentInput = z.infer<typeof stockAdjustmentSchema>;
