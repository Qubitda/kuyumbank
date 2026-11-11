import { z } from "zod";

export const salesChannelSchema = z.object({
  kod: z.string().trim().min(1, "Kanal kodu zorunludur."),
  ad: z.string().trim().min(1, "Kanal adı zorunludur."),
});

export type SalesChannelInput = z.infer<typeof salesChannelSchema>;
