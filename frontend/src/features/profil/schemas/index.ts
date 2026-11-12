import { z } from "zod";

export const profileSchema = z.object({
  first_name: z.string().trim().min(1, "Ad zorunludur."),
  last_name: z.string().trim().min(1, "Soyad zorunludur."),
});

export const passwordChangeSchema = z
  .object({
    current_password: z.string().min(1, "Mevcut şifre zorunludur."),
    new_password: z
      .string()
      .min(8, "Yeni şifre en az 8 karakter olmalıdır.")
      .regex(/[A-Za-z]/, "En az bir harf içermelidir.")
      .regex(/[0-9]/, "En az bir rakam içermelidir."),
    new_password_confirm: z.string().min(1, "Şifre tekrarı zorunludur."),
  })
  .refine((d) => d.new_password === d.new_password_confirm, {
    message: "Yeni şifreler eşleşmiyor.",
    path: ["new_password_confirm"],
  })
  .refine((d) => d.current_password !== d.new_password, {
    message: "Yeni şifre mevcut şifreden farklı olmalıdır.",
    path: ["new_password"],
  });

export const addressSchema = z.object({
  tip: z.enum(["TESLIMAT", "FATURA"], {
    message: "Geçerli bir adres tipi seçin.",
  }),
  il: z.string().trim().min(2, "İl zorunludur."),
  ilce: z.string().trim().optional(),
  adres: z.string().trim().min(5, "Açık adres en az 5 karakter olmalıdır."),
  varsayilan: z.boolean().optional(),
});

export const emailVerifyConfirmSchema = z.object({
  uid: z.string().trim().min(1, "uid zorunludur."),
  token: z.string().trim().min(1, "token zorunludur."),
});

export type ProfileInput = z.infer<typeof profileSchema>;
export type PasswordChangeInput = z.infer<typeof passwordChangeSchema>;
export type AddressInput = z.infer<typeof addressSchema>;
export type EmailVerifyConfirmInput = z.infer<typeof emailVerifyConfirmSchema>;
