"use client";

import { LoginForm, useAuth } from "@/features/auth";
import { ThemeToggle } from "@/components/layout";
import { DomainLoading } from "@/components/route-states";

export default function LoginPage() {
  const { loading, isAuthenticated, mfaPending } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <DomainLoading label="Oturum" />
      </div>
    );
  }

  if (isAuthenticated && !mfaPending) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <DomainLoading label="Panele yönlendirme" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen w-full flex-col bg-background">
      <header
        className="flex h-[56px] w-full items-center justify-between border-b border-border px-4 sm:px-6"
        role="banner"
      >
        <div className="flex items-center gap-2 font-semibold text-foreground tracking-tight text-base">
          <span
            className="flex h-6 w-6 items-center justify-center rounded-[4px] bg-primary text-primary-foreground font-mono text-xs"
            aria-hidden="true"
          >
            K
          </span>
          <span>Kuyumbank</span>
        </div>
        <ThemeToggle />
      </header>

      <main
        id="login-main"
        className="flex flex-1 items-center justify-center p-4 sm:p-8"
        aria-labelledby="login-heading"
      >
        <div className="flex w-full max-w-[420px] flex-col items-center gap-6">
          <div className="flex flex-col items-center gap-1.5 text-center px-2">
            <h1
              id="login-heading"
              className="text-2xl font-semibold tracking-tight text-foreground"
            >
              Kuyumbank
            </h1>
            <p className="text-xs text-muted-foreground max-w-[32ch] leading-relaxed">
              Jewelry B2B Commerce & Trading Platform — güvenli firma oturumu
            </p>
          </div>

          <LoginForm />

          <p className="text-[11px] text-muted-foreground text-center max-w-[36ch]">
            Yetki matrisi, tenant izolasyonu ve MFA kontrolü backend otoritesindedir.
          </p>
        </div>
      </main>
    </div>
  );
}
