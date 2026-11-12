import { z } from "zod";

/** OpenAPI TakipNoRequest — tasiyici yok (GAP-F4-01). */
export const shipmentDispatchSchema = z.object({
  takip_no: z.string().trim().min(1, "Takip numarası zorunludur."),
});

export type ShipmentDispatchInput = z.infer<typeof shipmentDispatchSchema>;

export const shipmentPodSchema = z.object({
  teslim_alan: z.string().trim().min(1, "Teslim alan zorunlu."),
  notlar: z.string().trim().optional(),
  belgeler_ref: z.string().trim().optional(),
});

export type ShipmentPodInput = z.infer<typeof shipmentPodSchema>;
