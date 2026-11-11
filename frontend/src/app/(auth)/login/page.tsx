import { Suspense } from "react";

import { LoginForm } from "@/features/auth";

export default function LoginPage() {
  return (
    <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center gap-8 px-6 py-16">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Giriş</h1>
        <p className="text-sm text-muted-foreground">
          Session + CSRF · rolünüze göre portal.
        </p>
      </header>
      <Suspense
        fallback={
          <p className="text-sm text-muted-foreground">Yükleniyor…</p>
        }
      >
        <LoginForm />
      </Suspense>
    </div>
  );
}
