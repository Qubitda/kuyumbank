"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { loginSchema, type LoginInput } from "../schemas/login";
import { authService } from "../services/auth-service";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle } from "lucide-react";

export function LoginForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginInput) => {
    setServerError(null);
    try {
      await authService.login(data.username, data.password);
      router.push("/");
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(
          err.problem.detail ||
            err.problem.title ||
            "Giriş bilgileri doğrulanamadı."
        );
      } else {
        setServerError("Giriş sırasında sunucu bağlantı hatası oluştu.");
      }
    }
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex w-full max-w-[420px] flex-col gap-5 rounded-[8px] border border-border bg-card p-6 shadow-none"
      noValidate
    >
      <div className="flex flex-col gap-1 border-b border-border pb-3">
        <h2 className="text-base font-semibold tracking-tight text-foreground">
          Platform Girişi
        </h2>
        <p className="text-xs text-muted-foreground">
          Session cookie & CSRF ile güvenli oturum. Tarayıcıda token tutulmaz.
        </p>
      </div>

      {serverError && (
        <div
          className="flex items-center gap-2 rounded-[6px] border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive"
          role="alert"
        >
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{serverError}</span>
        </div>
      )}

      {/* Kullanıcı Adı */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="login-username">Kullanıcı Adı</Label>
        <Input
          id="login-username"
          type="text"
          autoComplete="username"
          placeholder="Örn: platform_admin veya alici_demo"
          disabled={isSubmitting}
          aria-invalid={Boolean(errors.username)}
          {...register("username")}
        />
        {errors.username && (
          <span className="text-[11px] text-destructive">
            {errors.username.message}
          </span>
        )}
      </div>

      {/* Parola */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="login-password">Parola</Label>
        <Input
          id="login-password"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
          disabled={isSubmitting}
          aria-invalid={Boolean(errors.password)}
          {...register("password")}
        />
        {errors.password && (
          <span className="text-[11px] text-destructive">
            {errors.password.message}
          </span>
        )}
      </div>

      <div className="pt-2">
        {/* Tek Primary Buton Kuralı */}
        <Button
          type="submit"
          className="w-full"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Giriş yapılıyor…" : "Giriş Yap"}
        </Button>
      </div>

      <div className="text-[11px] text-muted-foreground text-center">
        <span>Yetki matrisi ve tenant izolasyonu backend otoritesindedir.</span>
      </div>
    </form>
  );
}
