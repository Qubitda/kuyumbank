import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Tailwind class merge — shadcn `cn`. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Commerce yazma — Idempotency-Key. */
export function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `ik-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}
