import { z } from "zod";

export const orgUnitSchema = z.object({
  ad: z.string().trim().min(1, "Birim adı zorunludur."),
  kod: z.string().trim().min(1, "Birim kodu zorunludur."),
  tip: z.string().optional(),
});

export type OrgUnitInput = z.infer<typeof orgUnitSchema>;
