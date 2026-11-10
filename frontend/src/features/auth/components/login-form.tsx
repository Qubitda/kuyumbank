"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { ApiError, login } from "@/lib/api/client";

export function LoginForm() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function onSubmit(formData: FormData) {
    const username = String(formData.get("username") || "").trim();
    const password = String(formData.get("password") || "");
    setError(null);
    startTransition(async () => {
      try {
        await login(username, password);
        router.replace("/");
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
        <label htmlFor="username" className="text-xs font-medium text-muted-foreground">
          Kullanıcı adı
        </label>
        <input
          id="username"
          name="username"
          autoComplete="username"
          required
          className="h-10 rounded-md border border-border bg-background px-3 text-sm outline-none ring-ring focus:ring-2"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor="password" className="text-xs font-medium text-muted-foreground">
          Parola
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className="h-10 rounded-md border border-border bg-background px-3 text-sm outline-none ring-ring focus:ring-2"
        />
      </div>
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={pending}
        className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground disabled:opacity-50"
      >
        {pending ? "Giriş yapılıyor…" : "Giriş yap"}
      </button>
    </form>
  );
}
