import { z } from "zod";

export const shipmentDispatchSchema = z.object({
  takip_no: z.string().trim().min(1, "Takip numarası zorunludur."),
  tasiyici: z.string().trim().min(1, "Taşıyıcı firma zorunludur."),
});

export type ShipmentDispatchInput = z.infer<typeof shipmentDispatchSchema>;
