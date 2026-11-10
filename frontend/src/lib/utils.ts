/** Genel sınıf birleştirme — shadcn `cn` sonrası genişletilebilir. */
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}
