"use client";

import { useEffect } from "react";
import Link from "next/link";

export function DomainLoading({ label }: { label: string }) {
  return (
    <p className="text-sm text-muted-foreground" aria-live="polite">
      {label} yükleniyor…
    </p>
  );
}

export function DomainError({
  label,
  error,
  reset,
}: {
  label: string;
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(`[${label}]`, error);
  }, [label, error]);

  return (
    <div className="flex flex-col gap-3" role="alert">
      <p className="text-sm text-destructive">
        {label} yüklenemedi.
        {error.message ? (
          <span className="mt-1 block text-muted-foreground">{error.message}</span>
        ) : null}
      </p>
      <div className="flex gap-3 text-sm">
        <button
          type="button"
          onClick={reset}
          className="h-9 rounded-md border border-border px-3 font-medium"
        >
          Yeniden dene
        </button>
        <Link href="/" className="inline-flex h-9 items-center underline-offset-4 hover:underline">
          Ana sayfa
        </Link>
      </div>
    </div>
  );
}

export function DomainPlaceholder({
  title,
  backendApp,
  note,
}: {
  title: string;
  backendApp: string;
  note?: string;
}) {
  return (
    <div className="flex flex-col gap-3">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="text-sm text-muted-foreground">
        Feature iskeleti hazır. Backend app:{" "}
        <code className="font-mono text-xs">{backendApp}</code>
      </p>
      {note ? <p className="text-sm text-muted-foreground">{note}</p> : null}
      <p className="text-xs text-muted-foreground">
        Feature: <code className="font-mono">features/{backendApp}</code> · rehber:{" "}
        <code className="font-mono">docs/FRONTEND_ARCHITECTURE.md</code>
      </p>
    </div>
  );
}
