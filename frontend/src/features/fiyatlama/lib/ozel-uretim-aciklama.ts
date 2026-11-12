/**
 * OpenAPI RfqCreateRequest line alanları: miktar, birim?, varyant_id?, aciklama?
 * Montür/taş/ayar/gram first-class alan olmadığı için aciklama’ya kodlanır (GAP-F3-05).
 */
export function buildOzelUretimAciklama(input: {
  monturAd?: string;
  monturVaryantId?: number;
  tasOzeti?: string;
  hedefAyar?: string;
  hedefGram?: string;
  not?: string;
}): string {
  const parts: string[] = ["[OZEL_URETIM]"];
  if (input.monturVaryantId) {
    parts.push(`montur_varyant_id=${input.monturVaryantId}`);
  }
  if (input.monturAd?.trim()) {
    parts.push(`montur=${input.monturAd.trim()}`);
  }
  if (input.tasOzeti?.trim()) {
    parts.push(`tas=${input.tasOzeti.trim()}`);
  }
  if (input.hedefAyar?.trim()) {
    parts.push(`ayar=${input.hedefAyar.trim()}`);
  }
  if (input.hedefGram?.trim()) {
    parts.push(`gram=${input.hedefGram.trim()}`);
  }
  if (input.not?.trim()) {
    parts.push(input.not.trim());
  }
  return parts.join(" | ").slice(0, 255);
}
