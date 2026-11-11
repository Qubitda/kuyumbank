"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { SessionProvider, useSession } from "@/features/auth/components/session-provider";
import { portalHomeForMe } from "@/lib/auth/portal";

function HomeRedirect() {
  const { state } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (state.status === "ready") {
      router.replace(portalHomeForMe(state.me));
    }
  }, [state, router]);

  if (state.status === "loading") {
    return (
      <p className="text-sm text-muted-foreground">Oturum kontrol ediliyor…</p>
    );
  }

  if (state.status === "ready") {
    return (
      <p className="text-sm text-muted-foreground">Portala yönlendiriliyor…</p>
    );
  }

  if (state.status === "error") {
    return (
      <p className="text-sm text-destructive" role="alert">
        {state.message}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">Oturum yok.</p>
      <Link
        href="/login"
        className="inline-flex h-10 w-fit items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
      >
        Giriş yap
      </Link>
    </div>
  );
}

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-lg flex-1 flex-col gap-8 px-6 py-16">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">Kuyumbank</h1>
        <p className="text-sm text-muted-foreground">
          B2B portal — rolünüze göre müşteri, tedarikçi veya admin alanı.
        </p>
      </header>
      <SessionProvider>
        <HomeRedirect />
      </SessionProvider>
    </div>
  );
}
