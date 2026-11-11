import Link from "next/link";
import { LoginForm } from "@/features/auth";
import { ThemeToggle } from "@/components/layout";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen w-full flex-col bg-background">
      {/* Basit Header */}
      <header className="flex h-[56px] w-full items-center justify-between border-b border-border px-6">
        <Link
          href="/"
          className="flex items-center gap-2 font-semibold text-foreground tracking-tight text-base hover:opacity-90"
        >
          <span className="flex h-6 w-6 items-center justify-center rounded-[4px] bg-primary text-primary-foreground font-mono text-xs">
            K
          </span>
          <span>Kuyumbank</span>
        </Link>
        <ThemeToggle />
      </header>

      {/* Merkez Form */}
      <main className="flex flex-1 items-center justify-center p-6">
        <div className="flex w-full max-w-[420px] flex-col items-center gap-6">
          <div className="flex flex-col items-center gap-1 text-center">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Kuyumbank
            </h1>
            <p className="text-xs text-muted-foreground">
              Jewelry B2B Commerce & Trading Platform
            </p>
          </div>

          <LoginForm />

          <div className="text-xs text-muted-foreground text-center">
            <Link
              href="/"
              className="text-foreground underline-offset-4 hover:underline font-medium"
            >
              ← Portala Dön
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
