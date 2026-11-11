import { z } from "zod";

export const loginSchema = z.object({
  username: z
    .string()
    .trim()
    .min(1, "Kullanıcı adı boş bırakılamaz."),
  password: z
    .string()
    .min(1, "Parola boş bırakılamaz."),
});

export type LoginInput = z.infer<typeof loginSchema>;
