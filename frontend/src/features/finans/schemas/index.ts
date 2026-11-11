import { z } from "zod";

export const paymentIntentSchema = z.object({
  tutar: z.string().min(1, "Tutar zorunludur."),
  para_birimi: z.string().min(1, "Para birimi zorunludur."),
  siparis_id: z.number().int().positive().optional(),
});

export type PaymentIntentInput = z.infer<typeof paymentIntentSchema>;
