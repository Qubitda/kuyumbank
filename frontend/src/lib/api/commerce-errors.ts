import { ApiError } from "./client";

/**
 * Checkout / sepet yazma hatalarını kullanıcı diline çevirir.
 * Kod/mesaj OpenAPI ProblemDetail’den gelir; yeni endpoint uydurulmaz.
 */
export function mapCommerceError(err: unknown, fallback: string): string {
  if (!(err instanceof ApiError)) {
    return err instanceof Error ? err.message : fallback;
  }

  const code = String(err.problem.code || "").toLowerCase();
  const text = `${err.problem.detail || ""} ${err.problem.title || ""}`.toLowerCase();
  const blob = `${code} ${text}`;

  if (
    /stock|stok|oversell|yetersiz.?stok|insufficient.?stock|reservation/.test(
      blob
    )
  ) {
    return "Stok yetersiz veya rezervasyon kurulamadı. Sepeti güncelleyin.";
  }
  if (/credit|kredi|limit|insufficient.?credit|musait/.test(blob)) {
    return "Kredi limiti yetersiz. Tutarı düşürün veya finans birimiyle görüşün.";
  }
  if (
    /quote.*expir|expir.*quote|süre.?si.?dol|gecerlilik|geçerlilik|ttl|stale.?quote/.test(
      blob
    )
  ) {
    return "Quote süresi dolmuş. Katalogdan yeni fiyat alın veya fiyatlama ekranından yenileyin.";
  }
  if (/idempotency|tekrar|replay/.test(blob)) {
    return err.problem.detail || "İstek yinelenmiş olabilir; siparişleri kontrol edin.";
  }

  return err.problem.detail || err.problem.title || err.message || fallback;
}
