import { z } from "zod";

export const catalogFilterSchema = z.object({
  q: z.string().optional(),
  ordering: z.string().optional(),
  page: z.coerce.number().int().positive().optional(),
  page_size: z.coerce.number().int().positive().optional(),
  onay_durumu: z.string().optional(),
  yayin_durumu: z.string().optional(),
});

export const opsProductCreateSchema = z.object({
  ad: z.string().trim().min(1, "Ürün adı zorunludur."),
  kategori_id: z
    .number({ message: "kategori_id zorunludur." })
    .int()
    .positive("kategori_id zorunludur."),
  ayar_id: z
    .number({ message: "ayar_id zorunludur." })
    .int()
    .positive("ayar_id zorunludur."),
  aciklama: z.string().trim().optional(),
  fiyat_tipi: z.string().trim().optional(),
  satis_kanali_id: z.number().int().positive().optional(),
});

export const opsVariantCreateSchema = z.object({
  gram: z.string().trim().optional(),
  renk_id: z.number().int().positive().optional(),
  ek_bedel: z.string().trim().optional(),
});

export const rejectSchema = z.object({
  neden: z.string().trim().min(1, "Red nedeni zorunludur."),
});

export type CatalogFilterInput = z.infer<typeof catalogFilterSchema>;
export type OpsProductCreateInput = z.infer<typeof opsProductCreateSchema>;
export type OpsVariantCreateInput = z.infer<typeof opsVariantCreateSchema>;
export type RejectInput = z.infer<typeof rejectSchema>;
