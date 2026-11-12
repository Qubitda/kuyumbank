import { z } from "zod";

export const orgUnitSchema = z.object({
  kod: z.string().trim().min(2, "Birim kodu en az 2 karakter olmalıdır."),
  ad: z.string().trim().min(2, "Birim adı en az 2 karakter olmalıdır."),
  parent_id: z.number().nullable().optional(),
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
  email: z.string().email("Geçerli bir e-posta adresi girin.").optional().or(z.literal("")),
  phone: z.string().optional(),
});

export type OrgUnitInput = z.infer<typeof orgUnitSchema>;
export type AddressInput = z.infer<typeof addressSchema>;
export type ProfileInput = z.infer<typeof profileSchema>;
