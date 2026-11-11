/**
 * Görüntü formatları.
 * Nihai para/gram hesabı backend otoritesindedir (API_CONTRACT & ADR-0017).
 * Locale: tr-TR (Django LANGUAGE_CODE ile birebir paralel).
 */

export function formatMoney(
  value: string | number | null | undefined,
  currency = "TRY",
  locale = "tr-TR"
): string {
  if (value === null || value === undefined) return "—";
  const n = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(n)) return String(value);

  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
}

export function formatGram(
  value: string | number | null | undefined,
  locale = "tr-TR",
  digits = 3
): string {
  if (value === null || value === undefined) return "—";
  const n = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(n)) return String(value);

  return `${new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  }).format(n)} g`;
}

export function formatDateTime(
  iso: string | null | undefined,
  locale = "tr-TR",
  timeZone = "Europe/Istanbul"
): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "short",
    timeStyle: "short",
    timeZone,
  }).format(d);
}

export function formatPercent(
  value: string | number | null | undefined,
  locale = "tr-TR",
  digits = 2
): string {
  if (value === null || value === undefined) return "—";
  const n = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(n)) return String(value);

  return `%${new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  }).format(n)}`;
}
