"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastTone = "success" | "error" | "info";

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  tone: ToastTone;
}

interface ToastContextValue {
  push: (input: {
    title: string;
    description?: string;
    tone?: ToastTone;
    durationMs?: number;
  }) => void;
  success: (title: string, description?: string) => void;
  error: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (input: {
      title: string;
      description?: string;
      tone?: ToastTone;
      durationMs?: number;
    }) => {
      const id = crypto.randomUUID
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random()}`;
      const tone = input.tone || "info";
      setItems((prev) => [
        ...prev.slice(-4),
        {
          id,
          title: input.title,
          description: input.description,
          tone,
        },
      ]);
      const ms = input.durationMs ?? (tone === "error" ? 7000 : 4000);
      window.setTimeout(() => dismiss(id), ms);
    },
    [dismiss]
  );

  const value = useMemo<ToastContextValue>(
    () => ({
      push,
      success: (title, description) =>
        push({ title, description, tone: "success" }),
      error: (title, description) => push({ title, description, tone: "error" }),
      info: (title, description) => push({ title, description, tone: "info" }),
    }),
    [push]
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-[min(100vw-2rem,22rem)] flex-col gap-2"
        aria-live="polite"
        aria-relevant="additions"
      >
        {items.map((t) => (
          <div
            key={t.id}
            role={t.tone === "error" ? "alert" : "status"}
            className={cn(
              "pointer-events-auto flex items-start gap-2 rounded-[8px] border bg-card p-3 text-xs shadow-sm",
              t.tone === "error" && "border-destructive/30",
              t.tone === "success" && "border-border",
              t.tone === "info" && "border-border"
            )}
          >
            {t.tone === "success" ? (
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-foreground" />
            ) : t.tone === "error" ? (
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
            ) : (
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            )}
            <div className="min-w-0 flex-1 space-y-0.5">
              <p className="font-medium text-foreground">{t.title}</p>
              {t.description ? (
                <p className="text-muted-foreground leading-relaxed">
                  {t.description}
                </p>
              ) : null}
            </div>
            <button
              type="button"
              className="rounded-[4px] p-0.5 text-muted-foreground hover:text-foreground"
              aria-label="Bildirimi kapat"
              onClick={() => dismiss(t.id)}
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast ToastProvider içinde kullanılmalıdır.");
  }
  return ctx;
}
