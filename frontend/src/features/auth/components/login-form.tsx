"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, login } from "@/lib/api/client";
import { portalHomeForMe } from "@/lib/auth/portal";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function onSubmit(formData: FormData) {
    const username = String(formData.get("username") || "").trim();
    const password = String(formData.get("password") || "");
    setError(null);
    startTransition(async () => {
      try {
        const me = await login(username, password);
        if (me.mfa_required && !me.mfa_ok) {
          setError("MFA gerekli — e-posta kodunu doğrulayın (yakında UI).");
          return;
        }
        const next = searchParams.get("next");
        const home = portalHomeForMe(me);
        const target =
          next && next.startsWith("/") && !next.startsWith("//") ? next : home;
        router.replace(target);
        router.refresh();
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.problem.detail || err.message);
        } else {
          setError("Giriş başarısız.");
        }
      }
    });
  }

  return (
    <form action={onSubmit} className="flex w-full max-w-sm flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="username">Kullanıcı adı</Label>
        <Input
          id="username"
          name="username"
          autoComplete="username"
          required
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="password">Parola</Label>
        <Input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </div>
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      <Button type="submit" disabled={pending}>
        {pending ? "Giriş yapılıyor…" : "Giriş yap"}
      </Button>
    </form>
  );
}
