import { z } from "zod";

export const documentFilterSchema = z.object({
  q: z.string().optional(),
  belge_tipi: z.string().optional(),
  durum: z.string().optional(),
  kaynak: z.string().optional(),
});

/** POD: binary upload yok — belgeler_ref harici anahtar/URL (F6-022). */
export const podAttachSchema = z.object({
  shipment_id: z
    .number({ message: "Sevkiyat seçin." })
    .int()
    .positive("Sevkiyat seçin."),
  teslim_alan: z.string().trim().min(1, "Teslim alan zorunludur."),
  notlar: z.string().trim().optional(),
  belgeler_ref: z
    .string()
    .trim()
    .max(255, "belgeler_ref en fazla 255 karakter.")
    .optional(),
});

export type DocumentFilterInput = z.infer<typeof documentFilterSchema>;
export type PodAttachInput = z.infer<typeof podAttachSchema>;
