import Link from "next/link";

import { LoginForm } from "@/features/auth";

export default function LoginPage() {
  return (
    <div className="mx-auto flex w-full max-w-md flex-1 flex-col gap-8 px-6 py-16">
      <header className="flex flex-col gap-2">
        <Link href="/" className="text-sm text-muted-foreground hover:underline">
          ← Kuyumbank
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">Giriş</h1>
        <p className="text-sm text-muted-foreground">
          Django session cookie. CSRF:{" "}
          <code className="font-mono text-xs">GET /api/v1/auth/csrf/</code>
        </p>
      </header>
      <LoginForm />
    </div>
  );
}
