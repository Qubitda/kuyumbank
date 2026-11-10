/**
 * Görüntü formatları. Nihai para/gram hesabı backend’de (API_CONTRACT).
 * Locale: tr-TR (Django LANGUAGE_CODE ile hizalı).
 */

export function formatMoney(
  value: string | number,
  currency = "TRY",
  locale = "tr-TR",
): string {
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
  value: string | number,
  locale = "tr-TR",
  digits = 3,
): string {
  const n = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(n)) return String(value);
  return `${new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  }).format(n)} g`;
}

export function formatDateTime(
  iso: string,
  locale = "tr-TR",
  timeZone = "Europe/Istanbul",
): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "short",
    timeStyle: "short",
    timeZone,
  }).format(d);
}
