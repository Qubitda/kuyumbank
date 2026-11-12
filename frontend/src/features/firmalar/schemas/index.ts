import { z } from "zod";

export const orgUnitSchema = z.object({
  kod: z.string().trim().min(1, "Birim kodu zorunludur."),
  ad: z.string().trim().min(1, "Birim adı zorunludur."),
  parent_id: z.number().nullable().optional(),
});

export const inviteSchema = z.object({
  email: z.string().trim().email("Geçerli bir e-posta adresi girin."),
  rol: z.string().trim().min(1, "Rol seçimi zorunludur."),
});

export const memberSchema = z.object({
  kullanici_id: z
    .number({ message: "Kullanıcı id zorunludur." })
    .int()
    .positive("Kullanıcı id zorunludur."),
});

export const approvalCreateSchema = z.object({
  tutar: z.string().trim().min(1, "Tutar zorunludur."),
  para_birimi: z.string().trim().optional(),
  order_id: z.coerce.number().int().positive().optional().or(z.nan()).optional(),
  org_birimi_id: z.coerce.number().int().positive().optional().or(z.nan()).optional(),
  gerekce: z.string().trim().optional(),
});

export const addressSchema = z.object({
  tip: z.enum(["TESLIMAT", "FATURA"], {
    message: "Lütfen geçerli bir adres tipi seçin.",
  }),
  il: z.string().trim().min(2, "İl zorunludur."),
  ilce: z.string().trim().optional(),
  adres: z.string().trim().min(5, "Açık adres en az 5 karakter olmalıdır."),
  varsayilan: z.boolean().optional(),
});

export const profileSchema = z.object({
  first_name: z.string().trim().min(1, "Ad zorunludur."),
  last_name: z.string().trim().min(1, "Soyad zorunludur."),
});

export type OrgUnitInput = z.infer<typeof orgUnitSchema>;
export type InviteInput = z.infer<typeof inviteSchema>;
export type MemberInput = z.infer<typeof memberSchema>;
export type ApprovalCreateInput = z.infer<typeof approvalCreateSchema>;
export type AddressInput = z.infer<typeof addressSchema>;
export type ProfileInput = z.infer<typeof profileSchema>;
