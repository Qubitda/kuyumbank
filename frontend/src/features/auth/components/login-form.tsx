"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { loginSchema, type LoginInput } from "../schemas/login";
import { authService } from "../services/auth-service";
import { useAuth } from "../hooks/use-auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle, Eye, EyeOff, Loader2, ShieldCheck } from "lucide-react";

const mfaSchema = z.object({
  code: z
    .string()
    .trim()
    .min(4, "Doğrulama kodu en az 4 karakter olmalıdır.")
    .max(12, "Doğrulama kodu geçersiz."),
});

type MfaInput = z.infer<typeof mfaSchema>;

function formatAuthError(err: unknown): string {
  if (err instanceof ApiError) {
    const fieldErrors = err.problem.errors;
    if (fieldErrors) {
      const parts = Object.entries(fieldErrors).flatMap(([key, val]) => {
        const messages = Array.isArray(val)
          ? val.map(String)
          : [String(val)];
        return messages.map((m) => `${key}: ${m}`);
      });
      if (parts.length) return parts.join(" · ");
    }
    return (
      err.problem.detail ||
      err.problem.title ||
      "Giriş bilgileri doğrulanamadı."
    );
  }
  if (err instanceof Error) return err.message;
  return "Giriş sırasında sunucu bağlantı hatası oluştu.";
}

export function LoginForm() {
  const navigate = useNavigate();
  const { setSessionUser, refresh } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [step, setStep] = useState<"credentials" | "mfa">("credentials");
  const [mfaHint, setMfaHint] = useState<string | null>(null);
  const [resending, setResending] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  });

  const mfaForm = useForm<MfaInput>({
    resolver: zodResolver(mfaSchema),
    defaultValues: { code: "" },
  });

  const onSubmitCredentials = async (data: LoginInput) => {
    setServerError(null);
    try {
      const me = await authService.login(data.username, data.password);
      if (me.mfa_required && !me.mfa_ok) {
        setSessionUser(null, { mfaPending: true });
        setStep("mfa");
        setMfaHint("E-posta adresinize gönderilen doğrulama kodunu girin.");
        return;
      }
      setSessionUser(me, { mfaPending: false });
      navigate("/", { replace: true });
    } catch (err) {
      setServerError(formatAuthError(err));
    }
  };

  const onSubmitMfa = async (data: MfaInput) => {
    setServerError(null);
    try {
      const me = await authService.verifyMfa(data.code);
      setSessionUser(me, { mfaPending: false });
      navigate("/", { replace: true });
    } catch (err) {
      setServerError(formatAuthError(err));
    }
  };

  const handleResendMfa = async () => {
    setResending(true);
    setServerError(null);
    try {
      const res = await authService.resendMfa();
      setMfaHint(res.detail || "Doğrulama kodu yeniden gönderildi.");
      if (res.mfa_ok) {
        await refresh();
        navigate("/", { replace: true });
      }
    } catch (err) {
      setServerError(formatAuthError(err));
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="flex w-full max-w-[420px] flex-col gap-5 rounded-[8px] border border-border bg-card p-6 sm:p-8">
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <h2 className="text-base font-semibold tracking-tight text-foreground">
          {step === "credentials" ? "Platform Girişi" : "İki Adımlı Doğrulama"}
        </h2>
        <p className="text-xs text-muted-foreground leading-relaxed">
          {step === "credentials"
            ? "Session cookie ve CSRF ile güvenli oturum. Tarayıcıda API token tutulmaz."
            : "MFA gerekli. Oturum, kod doğrulanana kadar portal erişimine kapalıdır."}
        </p>
      </div>

      {serverError && (
        <div
          className="flex items-start gap-2 rounded-[6px] border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive"
          role="alert"
        >
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{serverError}</span>
        </div>
      )}

      {step === "mfa" && mfaHint && !serverError && (
        <div className="flex items-start gap-2 rounded-[6px] border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
          <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5 text-foreground" />
          <span>{mfaHint}</span>
        </div>
      )}

      {step === "credentials" ? (
        <form
          onSubmit={handleSubmit(onSubmitCredentials)}
          className="flex flex-col gap-4"
          noValidate
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="login-username">Kullanıcı adı</Label>
            <Input
              id="login-username"
              type="text"
              autoComplete="username"
              autoFocus
              placeholder="kullanici_adi"
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

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="login-password">Parola</Label>
            <div className="relative">
              <Input
                id="login-password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="••••••••"
                disabled={isSubmitting}
                aria-invalid={Boolean(errors.password)}
                className="pr-10"
                {...register("password")}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-muted-foreground hover:text-foreground"
                aria-label={showPassword ? "Parolayı gizle" : "Parolayı göster"}
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {errors.password && (
              <span className="text-[11px] text-destructive">
                {errors.password.message}
              </span>
            )}
          </div>

          <Button type="submit" className="w-full mt-1" disabled={isSubmitting}>
            {isSubmitting ? (
              <span className="inline-flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Giriş yapılıyor…
              </span>
            ) : (
              "Giriş Yap"
            )}
          </Button>
        </form>
      ) : (
        <form
          onSubmit={mfaForm.handleSubmit(onSubmitMfa)}
          className="flex flex-col gap-4"
          noValidate
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="mfa-code">Doğrulama kodu</Label>
            <Input
              id="mfa-code"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              autoFocus
              placeholder="E-posta kodu"
              disabled={mfaForm.formState.isSubmitting}
              aria-invalid={Boolean(mfaForm.formState.errors.code)}
              className="font-mono tracking-widest"
              {...mfaForm.register("code")}
            />
            {mfaForm.formState.errors.code && (
              <span className="text-[11px] text-destructive">
                {mfaForm.formState.errors.code.message}
              </span>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={mfaForm.formState.isSubmitting}
          >
            {mfaForm.formState.isSubmitting ? (
              <span className="inline-flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Doğrulanıyor…
              </span>
            ) : (
              "Doğrula ve Devam Et"
            )}
          </Button>

          <div className="flex items-center justify-between gap-3 text-xs">
            <button
              type="button"
              className="text-muted-foreground hover:text-foreground underline-offset-4 hover:underline"
              onClick={() => {
                setStep("credentials");
                setServerError(null);
                setMfaHint(null);
                void authService.logout().catch(() => undefined);
                setSessionUser(null, { mfaPending: false });
              }}
            >
              ← Farklı hesap
            </button>
            <button
              type="button"
              className="text-foreground hover:underline underline-offset-4 disabled:opacity-50"
              disabled={resending}
              onClick={() => void handleResendMfa()}
            >
              {resending ? "Gönderiliyor…" : "Kodu yeniden gönder"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
