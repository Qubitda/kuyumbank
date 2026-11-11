import { z } from "zod";

export const cartAddSchema = z.object({
  varyant_id: z.number().int().positive("Geçerli bir varyant seçilmelidir."),
  miktar: z.number().int().positive("Miktar 1 veya daha fazla olmalıdır."),
});

export type CartAddInput = z.infer<typeof cartAddSchema>;

export const checkoutSchema = z.object({
  cart_id: z.number().int().positive(),
  teslimat_adresi_id: z.number().int().positive("Teslimat adresi seçilmelidir."),
});

export type CheckoutInput = z.infer<typeof checkoutSchema>;
