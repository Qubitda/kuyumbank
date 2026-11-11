import { z } from "zod";

export const documentUploadSchema = z.object({
  ad: z.string().trim().min(1, "Belge adı zorunludur."),
  belge_tipi: z.string().min(1, "Belge tipi seçilmelidir."),
});

export type DocumentUploadInput = z.infer<typeof documentUploadSchema>;
