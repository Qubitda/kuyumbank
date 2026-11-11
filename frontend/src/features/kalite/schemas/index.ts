import { z } from "zod";

export const measurementSchema = z.object({
  olculen_ayar: z.string().min(1, "Ayar değeri zorunludur."),
  olculen_gram: z.string().min(1, "Gram değeri zorunludur."),
  notlar: z.string().optional(),
});

export type MeasurementInput = z.infer<typeof measurementSchema>;
